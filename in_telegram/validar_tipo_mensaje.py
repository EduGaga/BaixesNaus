# in_telegram/validar_tipo_mensaje.py

import logging
from telegram import Update 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def es_mensaje_de_texto(telegram_message_update: dict) -> bool:
    try:
        if 'message' in telegram_message_update and telegram_message_update['message'].get('text') is not None:
            logger.info("Mensaje inicial detectado: ¡Es un mensaje de TEXTO!")
            return True
        else:
            logger.info("Mensaje inicial detectado: NO es un mensaje de texto (es otro tipo de contenido o un evento).")
            return False
    except Exception as e:
        logger.error(f"Error al verificar el tipo de mensaje: {e}. Update recibido: {telegram_message_update}")
        return False
