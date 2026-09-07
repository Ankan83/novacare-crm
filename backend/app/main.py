from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from app.api.exception_handlers import register_exception_handlers
from app.api.chat import router as chat_router
from app.api.crm import router as crm_router
from app.database.session import Base, engine
from app.models import HCP, Interaction
from app.core.config import settings


app = FastAPI(
    title="Nova AI CRM",
    version="1.0.0",
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    chat_router,
    prefix="/api",
)
app.include_router(
    crm_router,
    prefix="/api",
)


@app.on_event("startup")
def create_database_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "message": "Nova AI CRM Backend Running 🚀"
    }