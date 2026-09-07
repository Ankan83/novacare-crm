from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from app.api.exception_handlers import register_exception_handlers
from app.api.chat import router as chat_router
from app.api.crm import router as crm_router


app = FastAPI(
    title="Nova AI CRM",
    version="1.0.0",
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
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


@app.get("/")
def root():
    return {
        "message": "Nova AI CRM Backend Running 🚀"
    }