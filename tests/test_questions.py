
def create_test_user(client):
    response = client.post(
        "/users",
        json={
            "name": "Question Test User",
            "email": "questiontest@example.com"
        }
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_add_question_credits(client):
    user_id = create_test_user(client)

    response = client.post(
        "/questions/add",
        json={
            "user_id": user_id,
            "amount": 5
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["questions_added"] == 5
    assert data["remaining_balance"] == 8


def test_add_questions_for_invalid_user(client):
    response = client.post(
        "/questions/add",
        json={
            "user_id": 9999,
            "amount": 5
        }
    )

    assert response.status_code == 404


def test_question_history_empty(client):
    user_id = create_test_user(client)

    response = client.get(f"/questions/history/{user_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user_id
    assert data["total_questions"] == 0
    assert data["history"] == []


def test_question_history_for_invalid_user(client):
    response = client.get("/questions/history/9999")

    assert response.status_code == 404



def test_ask_question_without_credits(client, db_session):
    from app.models.user import User

    user_id = create_test_user(client)

    user = db_session.query(User).filter(User.id == user_id).first()
    user.question_balance = 0
    db_session.commit()

    response = client.post(
        "/questions/ask",
        json={
            "user_id": user_id,
            "question": "What is my ascendant?"
        }
    )

    assert response.status_code == 403
    assert "Insufficient question balance" in response.json()["detail"]
