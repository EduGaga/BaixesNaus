# in_telegram/verificar_uuid.py
import json
import os
import logging

# Configuración del logging para este módulo
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ruta al archivo de IDs
USER_IDS_FILE = 'in_telegram/telegram-clientes.json'

def _load_user_ids(file_path):
    """
    Carga la lista de IDs de usuario desde un archivo JSON.
    Retorna una lista de enteros con los IDs.
    """
    if not os.path.exists(file_path):
        logger.error(f"Error: El archivo de IDs de usuario no se encontró en '{file_path}'.")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ids_list = json.load(f)
            if not isinstance(ids_list, list):
                logger.error(f"Error: El formato del archivo '{file_path}' no es una lista JSON.")
                return []
            return [int(uid) for uid in ids_list if isinstance(uid, (int, str)) and str(uid).isdigit()]
    except json.JSONDecodeError as e:
        logger.error(f"Error de formato JSON en '{file_path}': {e}. Se usará una lista vacía.")
        return []
    except Exception as e:
        logger.error(f"Error al cargar la lista de IDs desde '{file_path}': {e}. Se usará una lista vacía.")
        return []

# --- Función principal de verificación ---
def es_usuario_autorizado(telegram_message_update: dict) -> bool:
    """
    Verifica si el ID del usuario que envió el mensaje está en la lista blanca.
    """
    user_id = telegram_message_update.get('effective_user', {}).get('id') or \
              telegram_message_update.get('message', {}).get('from', {}).get('id')

    if user_id is None:
        logger.warning("No se pudo extraer el ID de usuario del mensaje.")
        return False

    authorized_ids = _load_user_ids(USER_IDS_FILE)

    if not authorized_ids:
        logger.warning(f"¡ATENCIÓN! La lista de IDs de usuario en '{USER_IDS_FILE}' está vacía o hubo un error al cargarla.")

    logger.info(f"Verificando usuario con ID: {user_id}")

    if user_id in authorized_ids:
        logger.info(f"Usuario {user_id} ENCONTRADO en la lista de IDs autorizados.")
        return True
    else:
        logger.info(f"Usuario {user_id} NO está en la lista de IDs autorizados.")
        return False
