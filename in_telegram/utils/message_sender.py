# in_telegram/utils/message_sender.py

import logging
from telegram.ext import ContextTypes # Necesario para el type hinting
import asyncio

logger = logging.getLogger(__name__)

async def send_message_async(chat_id: int, context: ContextTypes.DEFAULT_TYPE, message_text: str): # Función asíncrona para enviar un mensaje
    try:
        await context.bot.send_message(chat_id=chat_id, text=message_text)
        logger.info(f"Mensaje enviado a {chat_id}: '{message_text}'")
    except Exception as e:
        logger.error(f"Error al enviar mensaje a {chat_id}: {e}")

def send_message_sync_wrapper(chat_id: int, context: ContextTypes.DEFAULT_TYPE, message_text: str, main_loop: asyncio.AbstractEventLoop):#Función sincrona para enviar un mensaje
    asyncio.run_coroutine_threadsafe(
        send_message_async(chat_id, context, message_text),
        main_loop
    )