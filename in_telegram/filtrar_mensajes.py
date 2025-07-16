# in_telegram/filtrar_mensajes.py

import logging
import re
import asyncio
import time
from in_telegram.g_sheets.sheets import g_sheets

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def _send_message_async(chat_id: int, context, message_text: str):
    """Función asíncrona auxiliar para enviar un mensaje."""
    try:
        await context.bot.send_message(chat_id=chat_id, text=message_text)
        logger.info(f"Mensaje enviado a {chat_id}: '{message_text}'")
    except Exception as e:
        logger.error(f"Error al enviar mensaje a {chat_id}: {e}")

def _filtrar_nave(telegram_message_update: dict, context, main_loop: asyncio.AbstractEventLoop) -> None:

    user_id = telegram_message_update.get('effective_user', {}).get('id', 'N/A')
    chat_id = telegram_message_update.get('message', {}).get('chat', {}).get('id')
    message_content = telegram_message_update.get('message', {}).get('text')

    if not message_content:
        logger.debug("Contenido de mensaje vacío para filtrar_nave.")
        return

    # Convertir a minúsculas y eliminar espacios extra para una mejor comparación
    processed_message = message_content.strip().lower()

    message_without_sac = processed_message.replace("sac", "").strip()

    #Normalizar espacios
    normalized_message = re.sub(r'\s+', ' ', message_without_sac).strip()
    
      # Contar las letras y los números.
    letras_encontradas = re.findall(r'[a-zñç]', normalized_message, re.UNICODE)
    numeros_encontrados = re.findall(r'\d', normalized_message)

    # Verificar que el resto del contenido, sin letras, números ni espacios, sea vacío.
    # Esto asegura que SÓLO haya letras, números y espacios.
    # Patron para todos los caracteres permitidos en este filtro (letras, números, espacios)
    patron_permitidos_nave = re.compile(r"^[a-z0-9\sñç]+$", re.UNICODE)

    # Si contiene algo que no sea una letra, un 'sac', un número o un espacio, no es válido para este filtro.
    if not patron_permitidos_nave.fullmatch(normalized_message):
        logger.info(f"Sub-filtro 'nave' para '{message_content}' NO PASADO: Contiene caracteres no permitidos fuera de letra/número/espacio/sac.")
        response_text = "El format no es correcte. Només està permès utilitzar caràcters alfanumèrics." 
        asyncio.run_coroutine_threadsafe(
            _send_message_async(chat_id, context, response_text),
            main_loop)
        return

    # La condición de "una sola letra y uno o varios números"
    is_strictly_ln_pattern = (len(letras_encontradas) == 1 and len(numeros_encontrados) >= 1)

    if is_strictly_ln_pattern:
        logger.info(f"Sub-filtro 'nave' para '{message_content}' PASADO (patrón letra+números y sac: OK).")
        g_sheets(telegram_message_update, context, main_loop)
    else:
        logger.info(f"Sub-filtro 'nave' para '{message_content}' NO PASADO: Contiene caracteres no permitidos fuera de letra/número/espacio/sac.")
        response_text = "El format no es correcte. " 
        asyncio.run_coroutine_threadsafe(
            _send_message_async(chat_id, context, response_text),
            main_loop)
        time.sleep(0.1)
        response_text = "El format correcte està compost pel Nº de baixes, la lletra de la nau i si és un sacrificat ha de contenir 'sac'."
        asyncio.run_coroutine_threadsafe(
            _send_message_async(chat_id, context, response_text),
            main_loop)
    return

def filtrar(telegram_message_update: dict, context, main_loop: asyncio.AbstractEventLoop) -> None:
    user_id = telegram_message_update.get('effective_user', {}).get('id', 'N/A')
    chat_id = telegram_message_update.get('message', {}).get('chat', {}).get('id')
    
    try:
        message_content = telegram_message_update.get('message', {}).get('text')

        if message_content is None:
            logger.info(f"Usuario {user_id}: El mensaje no tiene contenido de texto para filtrar.")
            return 
        
        patron = re.compile(r"^[a-zA-Z0-9\sÑñÇç]+$", re.UNICODE)
                
        try:
            if not patron.fullmatch(message_content):
                logger.info(f"Usuario {user_id}: Mensaje '{message_content}' NO cumple con el filtro de caracteres.")
                error_text = "Només s'admeten caràcters alfanumèrics."
                asyncio.run_coroutine_threadsafe(
                _send_message_async(chat_id, context, error_text),
                main_loop)
            else:
                logger.info(f"Usuario {user_id}: Mensaje '{message_content}' cumple con el filtro (todo ok).")
                _filtrar_nave(telegram_message_update, context, main_loop)
        except Exception as send_e:
            logger.error(f"Error al intentar enviar el mensaje de respuesta a {user_id}: {send_e}")
            
    except Exception as e:
        logger.error(f"Error general en la función de filtrado para el usuario {user_id}: {e}")

        