
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.user_routes import router as user_router
from app.api.chart_routes import router as chart_router
from app.api.question_routes import router as question_router

app = FastAPI(
    title="Melooha AI",
    description="Grounded Astrology Question Answering Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
       "https://melooha-frontend.vercel.app",
       ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(chart_router)
app.include_router(question_router)


@app.get("/")
def home():
    return {
        "message": "Melooha AI Backend is running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
