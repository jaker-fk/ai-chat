from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.database import init_db
from backend.core.exceptions import register_exception_handlers
from backend.routers.auth import router as auth_router
from backend.routers.chat import router as chat_router
from backend.routers.knowledge import router as knowledge_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI 对话应用", lifespan=lifespan)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(knowledge_router)


@app.get("/")
def root():
    return {"message": "AI 对话应用 running"}


@app.get("/health")
def health():
    return {"status": "ok"}
