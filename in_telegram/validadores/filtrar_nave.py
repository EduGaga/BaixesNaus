# in_telegram/validadores/filtrar_nave.py

import logging
import re
import asyncio
import time
from telegram.ext import ContextTypes
from in_telegram.g_sheets.baixes_g_sheets import g_sheets 
from in_telegram.utils.message_sender import send_message_sync_wrapper 
from in_telegram.validadores.llista_naus_valides import llista_naus_valides

logger = logging.getLogger(__name__)


#    Función para filtrar y procesar mensajes relacionados con datos de nave.
def filtrar_nave(telegram_message_update: dict, context: ContextTypes.DEFAULT_TYPE, main_loop: asyncio.AbstractEventLoop) -> None:
    user_id = telegram_message_update.get('effective_user', {}).get('id', 'N/A')
    chat_id = telegram_message_update.get('message', {}).get('chat', {}).get('id')
    message_content = telegram_message_update.get('message', {}).get('text')

    if not message_content:
        logger.debug("Contenido de mensaje vacío para filtrar_nave.")
        return

    # Convertir a minúsculas y eliminar espacios extra para una mejor comparación
    processed_message = message_content.strip().lower()

    message_without_sac = processed_message.replace("sac", "").strip()

    # Normalizar espacios
    normalized_message = re.sub(r'\s+', ' ', message_without_sac).strip()
    
    # Contar las letras y los números.
    letras_encontradas = re.findall(r'[a-zñç]', normalized_message, re.UNICODE)
    numeros_encontrados = re.findall(r'\d', normalized_message)

    # Verificar que el resto del contenido, sin letras, números ni espacios, sea vacío.
    patron_permitidos_nave = re.compile(r"^[a-z0-9\sñç]+$", re.UNICODE)

    if not patron_permitidos_nave.fullmatch(normalized_message):
        logger.info(f"Sub-filtro 'nave' para '{message_content}' NO PASADO: Contiene caracteres no permitidos fuera de letra/número/espacio/sac.")
        response_text = "El format no es correcte. Només està permès utilitzar caràcters alfanumèrics." 
        send_message_sync_wrapper(chat_id, context, response_text, main_loop)
        return

    # La condición de "una sola letra y uno o varios números"
    is_strictly_ln_pattern = (len(letras_encontradas) == 1 and len(numeros_encontrados) >= 1)

    is_valid_nave_letter = False
    if is_strictly_ln_pattern:
        nave_letter = letras_encontradas[0] 
        if llista_naus_valides(nave_letter):
            is_valid_nave_letter = True

    if is_strictly_ln_pattern:
        if is_valid_nave_letter:
            logger.info(f"Sub-filtro 'nave' para '{message_content}' PASADO (patrón letra+números y sac: OK).")
            asyncio.run_coroutine_threadsafe(
                g_sheets(telegram_message_update, context, main_loop),
                main_loop
            )
        else:
            logger.info(f"Sub-filtro 'nave' para '{message_content}' NO PASADO: La letra de la nave no es válida.")
            response_text = "La lletra de la nau no és vàlida."
            send_message_sync_wrapper(chat_id, context, response_text, main_loop)

    else:
        logger.info(f"Sub-filtro 'nave' para '{message_content}' NO PASADO: Contiene caracteres no permitidos fuera de letra/número/espacio/sac.")
        response_text = "El format no es correcte. " 
        send_message_sync_wrapper(chat_id, context, response_text, main_loop)
        time.sleep(0.1) 
        response_text = "El format correcte està compost pel Nº de baixes, la lletra de la nau i si és un sacrificat ha de contenir 'sac'."
        send_message_sync_wrapper(chat_id, context, response_text, main_loop)
    return