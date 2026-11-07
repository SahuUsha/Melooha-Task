
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import queue
import threading

from app.db.database import get_db
from app.models.user import User
from app.models.question import Question
from app.models.transaction import Transaction


from fastapi.responses import StreamingResponse
from app.db.database import get_db, SessionLocal

from app.schemas.question import (
    QuestionAskRequest,
    QuestionTopUpRequest,
)
from datetime import timezone

from app.services.answer_service import answer_question

from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse


router = APIRouter(prefix="/questions", tags=["Questions"])


# ==========================================
# 1. ASK QUESTION
# ==========================================

@router.post("/ask")
def ask_question(
    request: QuestionAskRequest,
    db: Session = Depends(get_db),
):
    try:
        user = (
            db.query(User)
            .filter(User.id == request.user_id)
            .with_for_update()
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found.",
            )

        if user.question_balance <= 0:
            raise HTTPException(
                status_code=403,
                detail="Insufficient question balance. Please add questions.",
            )

        result = answer_question(
        db=db,
        question=request.question.strip(),
        user_id=user.id,
        top_k=5,
        )

        new_question = Question(
            user_id=user.id,
            question_text=request.question.strip(),
            answer=result["answer"],
            status="completed",
            llm_provider=result["provider"],
        )

        user.question_balance -= 1

        transaction = Transaction(
            user_id=user.id,
            transaction_type="question_deduction",
            amount=1,
            balance_after=user.question_balance,
            description="One question credit used.",
        )

        db.add(new_question)
        db.add(transaction)
        db.commit()
        db.refresh(new_question)

        return {
            "message": "Question answered successfully.",
            "question_id": new_question.id,
            "user_id": user.id,
            "question": new_question.question_text,
            "answer": result["answer"],
            "citations": result["citations"],
            "chart_citations": result["chart_citations"],
            "provider": result["provider"],
            "retrieved_count": result["retrieved_count"],
            "remaining_balance": user.question_balance,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        print(f"Question processing failed: {error}")

        raise HTTPException(
            status_code=500,
            detail="Failed to process question. No credit was deducted.",
        )


# ==========================================
# 2. ADD QUESTION CREDITS
# ==========================================

@router.post("/add")
def add_questions(
    request: QuestionTopUpRequest,
    db: Session = Depends(get_db),
):
    try:
        user = (
            db.query(User)
            .filter(User.id == request.user_id)
            .with_for_update()
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found.",
            )

        user.question_balance += request.amount

        transaction = Transaction(
            user_id=user.id,
            transaction_type="question_topup",
            amount=request.amount,
            balance_after=user.question_balance,
            description="Question credits added successfully.",
        )

        db.add(transaction)
        db.commit()
        db.refresh(user)

        return {
            "message": "Question credits added successfully.",
            "user_id": user.id,
            "questions_added": request.amount,
            "remaining_balance": user.question_balance,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        print(f"Question top-up failed: {error}")

        raise HTTPException(
            status_code=500,
            detail="Failed to add question credits.",
        )


@router.get("/history/{user_id}")
def get_question_history(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    questions = (
        db.query(Question)
        .filter(Question.user_id == user_id)
        .order_by(Question.created_at.desc())
        .all()
    )

    return {
        "user_id": user_id,
        "total_questions": len(questions),
        "history": [
            {
                "question_id": question.id,
                "question": question.question_text,
                "answer": question.answer,
                "status": question.status,
                "provider": question.llm_provider,
                "created_at": question.created_at,
            }
            for question in questions
        ],
    }


@router.post("/ask/stream")
def ask_question_stream(
    request: QuestionAskRequest,
    db: Session = Depends(get_db),
):
    # 1. Reserve one question credit.
    user = (
        db.query(User)
        .filter(User.id == request.user_id)
        .with_for_update()
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.question_balance <= 0:
        raise HTTPException(
            status_code=403,
            detail="No question credits remaining."
        )

    user.question_balance -= 1

    new_question = Question(
        user_id=user.id,
        question_text=request.question.strip(),
        status="processing",
    )

    transaction = Transaction(
        user_id=user.id,
        transaction_type="question_deduction",
        amount=1,
        balance_after=user.question_balance,
        description="One question credit reserved for streaming."
    )

    db.add(new_question)
    db.add(transaction)
    db.commit()
    db.refresh(new_question)

    question_id = new_question.id
    user_id = user.id
    question_text = request.question.strip()

    # 2. Create the SSE event generator.
    def event_stream():
        events = queue.Queue()
        finished = object()

        def generate_answer():
            worker_db = SessionLocal()

            try:
                def send_token(token):
                    if token is None:
                        events.put({
                            "event": "reset",
                            "data": {}
                        })
                    else:
                        events.put({
                            "event": "token",
                            "data": {"token": token}
                        })

                # Generate the grounded answer.
                result = answer_question(
                    db=worker_db,
                    question=question_text,
                    user_id=user_id,
                    top_k=5,
                    on_token=send_token,
                )

                # 3. Save the completed answer.
                question_record = (
                    worker_db.query(Question)
                    .filter(Question.id == question_id)
                    .first()
                )

                question_record.answer = result["answer"]
                question_record.status = "completed"
                question_record.llm_provider = result["provider"]

                worker_db.commit()

                updated_user = (
                    worker_db.query(User)
                    .filter(User.id == user_id)
                    .first()
                )

                events.put({
                    "event": "done",
                    "data": {
                        "question_id": question_id,
                        "answer": result["answer"],
                        "citations": result["citations"],
                        "chart_citations": result["chart_citations"],
                        "provider": result["provider"],
                        "retrieved_count": result["retrieved_count"],
                        "remaining_balance": updated_user.question_balance,
                    }
                })

            except Exception:
                worker_db.rollback()

                # 4. Mark the question as failed and refund the credit.
                try:
                    question_record = (
                        worker_db.query(Question)
                        .filter(Question.id == question_id)
                        .first()
                    )

                    user_record = (
                        worker_db.query(User)
                        .filter(User.id == user_id)
                        .with_for_update()
                        .first()
                    )

                    if question_record:
                        question_record.status = "failed"

                    if user_record:
                        user_record.question_balance += 1

                        refund = Transaction(
                            user_id=user_id,
                            transaction_type="question_refund",
                            amount=1,
                            balance_after=user_record.question_balance,
                            description="Credit refunded because answer generation failed."
                        )

                        worker_db.add(refund)

                    worker_db.commit()

                except Exception:
                    worker_db.rollback()

                events.put({
                    "event": "error",
                    "data": {
                        "message": "Answer generation failed. Your question credit has been refunded."
                    }
                })

            finally:
                worker_db.close()
                events.put(finished)

        # Run answer generation in a separate thread.
        thread = threading.Thread(
            target=generate_answer,
            daemon=True
        )
        thread.start()

        # Send events to the client as they arrive.
        while True:
            item = events.get()

            if item is finished:
                break

            event_name = item["event"]
            event_data = json.dumps(item["data"])

            yield f"event: {event_name}\ndata: {event_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
