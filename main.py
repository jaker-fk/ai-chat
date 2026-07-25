from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.database import init_db
from backend.routers.auth import router as auth_router
from backend.routers.chat import router as chat_router

app = FastAPI(title="AI 对话应用")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root():
    return {"message": "AI 对话应用 running"}


@app.get("/health")
def health():
    return {"status": "ok"}

