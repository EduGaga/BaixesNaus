# in_telegram/filtrar_mensajes.py

import logging
import re
import asyncio
from in_telegram.comandos.baixes_diaries import bajas_diarias_handler
from in_telegram.comandos.baixes_totals import mostrar_baixes_totals
from in_telegram.utils.message_sender import send_message_sync_wrapper 
from in_telegram.validadores.filtrar_nave import filtrar_nave

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def filtrar(telegram_message_update: dict, context, main_loop: asyncio.AbstractEventLoop) -> None:
    user_id = telegram_message_update.get('effective_user', {}).get('id', 'N/A')
    chat_id = telegram_message_update.get('message', {}).get('chat', {}).get('id')
    
    try:
        message_content = telegram_message_update.get('message', {}).get('text')

        print(f"Filtrando mensaje: '{message_content}' del chat {chat_id}")

        if message_content is None:
            logger.info(f"Usuario {user_id}: El mensaje no tiene contenido de texto para filtrar.")
            return 
        
        patron = re.compile(r"^[a-zA-Z0-9\sÑñÇç]+$", re.UNICODE)
                
        try:
            if message_content == "/mostrar_baixes_avui":
                bajas_diarias_handler(chat_id, context, main_loop)
            elif message_content == "/mostrar_baixes_totals":
                mostrar_baixes_totals(chat_id, context, main_loop)
            else:
                if not patron.fullmatch(message_content):
                    logger.info(f"Usuario {user_id}: Mensaje '{message_content}' NO cumple con el filtro de caracteres.")
                    error_text = "Només s'admeten caràcters alfanumèrics."
                    asyncio.run_coroutine_threadsafe(
                    send_message_sync_wrapper(chat_id, context, error_text),
                    main_loop)
                else:
                    logger.info(f"Usuario {user_id}: Mensaje '{message_content}' cumple con el filtro (todo ok).")
                    filtrar_nave(telegram_message_update, context, main_loop)
            
        except Exception as send_e:
            logger.error(f"Error al intentar enviar el mensaje de respuesta a {user_id}: {send_e}")
            
    except Exception as e:
        logger.error(f"Error general en la función de filtrado para el usuario {user_id}: {e}")

        