import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from exceptions import AppException
from logging_config import setup_logging
from models import Message
from schemas import APIResponse, MessageData, ReceiveRequest, ReceiveResponse, TranslateRequest
from services.translation import MockTranslationService, TranslationService

setup_logging()
logger = logging.getLogger("translation-api")

app = FastAPI(title="Translation Service")
translator: TranslationService = MockTranslationService()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("Application started and database initialized.")


@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException):
    logger.warning("Business exception raised: code=%s message=%s", exc.code, exc.message)
    return JSONResponse(
        status_code=400,
        content=APIResponse(success=False, code=exc.code, message=exc.message).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    logger.warning("Validation exception: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content=APIResponse(success=False, code=42201, message="参数校验失败", data=exc.errors()).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content=APIResponse(success=False, code=50000, message="服务器内部错误").model_dump(),
    )


@app.post("/receive", response_model=APIResponse[ReceiveResponse])
def receive(req: ReceiveRequest, db: Session = Depends(get_db)):
    message = Message(
        source_text=req.source_text,
        source_lang=req.source_lang,
        target_lang=req.target_lang,
        status="received",
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    logger.info("Received message id=%s", message.id)

    return APIResponse(data=ReceiveResponse(message_id=message.id, status=message.status))


@app.post("/translate", response_model=APIResponse[MessageData])
def translate(req: TranslateRequest, db: Session = Depends(get_db)):
    message = db.get(Message, req.message_id)
    if not message:
        raise AppException(code=40401, message="消息不存在")

    translated = translator.translate(
        text=message.source_text,
        source_lang=message.source_lang,
        target_lang=message.target_lang,
    )
    message.translated_text = translated
    message.status = "translated"
    db.add(message)
    db.commit()
    db.refresh(message)

    logger.info("Translated message id=%s", message.id)
    return APIResponse(data=MessageData.model_validate(message))


@app.get("/get/{message_id}", response_model=APIResponse[MessageData])
def get_message(message_id: int, db: Session = Depends(get_db)):
    message = db.get(Message, message_id)
    if not message:
        raise AppException(code=40401, message="消息不存在")

    logger.info("Fetched message id=%s", message.id)
    return APIResponse(data=MessageData.model_validate(message))
