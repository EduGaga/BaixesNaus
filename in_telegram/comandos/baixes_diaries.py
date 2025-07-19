# in_telegram/comandos/baixes_diaries.py

import logging
import asyncio
from telegram.ext import ContextTypes # Necesario para el type hinting
from in_telegram.utils.message_sender import send_message_sync_wrapper

logger = logging.getLogger(__name__)

def mostrar_baixes_diaries(chat_id: int, context: ContextTypes.DEFAULT_TYPE, main_loop: asyncio.AbstractEventLoop) -> None:  

    logger.info(f"Comando /mostrar_baixes_avui recibido del chat {chat_id}")

    mensaje_respuesta = "Aquí se mostrará el número de bajas de hoy."

    send_message_sync_wrapper(chat_id, context, mensaje_respuesta,main_loop)