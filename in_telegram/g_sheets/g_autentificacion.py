# in_telegram/g_sheets/g_autentificacion.py

import logging
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

_BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) 
_SECRETS_DIR = os.path.join(_BASE_PATH, 'secrets')
_SERVICE_ACCOUNT_FILE = os.path.join(_SECRETS_DIR, 'login.json')
_SPREADSHEET_ID_FILE = os.path.join(_SECRETS_DIR, 's_sheets.json')

_CREDENTIALS_RW = None # Credenciales de Lectura y Escritura
_CREDENTIALS_RO = None # Credenciales de Solo Lectura
_SPREADSHEET_ID = None

def _load_credentials_and_id():
    global _CREDENTIALS_RW, _CREDENTIALS_RO, _SPREADSHEET_ID
    if _CREDENTIALS_RW and _CREDENTIALS_RO and _SPREADSHEET_ID: # Ya cargadas
        return

    try:
        # 1. Cargar las credenciales de la cuenta de servicio (con ámbito de Lectura/Escritura)
        _CREDENTIALS_RW = service_account.Credentials.from_service_account_file(
            _SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets'] # Permiso completo (Lectura y Escritura)
        )
        
        # 2. Crear credenciales de solo lectura a partir de las credenciales RW
        _CREDENTIALS_RO = service_account.Credentials.from_service_account_file(
            _SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'] # Permiso de Solo Lectura
        )

        # 3. Cargar el ID de la hoja de cálculo
        with open(_SPREADSHEET_ID_FILE, 'r', encoding='utf-8') as f:
            spreadsheet_config = json.load(f)
            _SPREADSHEET_ID = spreadsheet_config.get('spreadsheet_id')
        
        if not _SPREADSHEET_ID:
            logger.error(f"Spreadsheet ID no encontrado en {_SPREADSHEET_ID_FILE}. Asegúrate de que el JSON contiene la clave 'spreadsheet_id'.")
            # Invalidar credenciales si falta ID
            _CREDENTIALS_RW = None 
            _CREDENTIALS_RO = None
            _SPREADSHEET_ID = None
            
        logger.info("Credenciales (RW/RO) y Spreadsheet ID de Google Sheets cargados correctamente.")

    except FileNotFoundError as e:
        logger.error(f"Archivo de credenciales o Spreadsheet ID no encontrado: {e}. Asegúrate de que 'sheets_service_account.json' y 'spreadsheet_id.json' están en '{_SECRETS_DIR}'.")
        _CREDENTIALS_RW = None
        _CREDENTIALS_RO = None
        _SPREADSHEET_ID = None
    except json.JSONDecodeError:
        logger.error(f"Error al decodificar JSON desde el archivo de configuración. Revisa el formato de '{_SERVICE_ACCOUNT_FILE}' o '{_SPREADSHEET_ID_FILE}'.")
        _CREDENTIALS_RW = None
        _CREDENTIALS_RO = None
        _SPREADSHEET_ID = None
    except Exception as e:
        logger.error(f"Error inesperado al cargar la configuración de Google Sheets: {e}")
        _CREDENTIALS_RW = None
        _CREDENTIALS_RO = None
        _SPREADSHEET_ID = None

_load_credentials_and_id()


def get_sheets_service_rw():# Permiso de Lectura y Escritura
    if not _CREDENTIALS_RW:
        logger.error("No se pudieron obtener credenciales de LECTURA/ESCRITURA. No se puede construir el servicio de Sheets.")
        return None
    try:
        return build('sheets', 'v4', credentials=_CREDENTIALS_RW)
    except Exception as e:
        logger.error(f"Error al construir el servicio de Google Sheets (RW): {e}")
        return None

def get_sheets_service_ro():#solo permiso de lectura
    if not _CREDENTIALS_RO:
        logger.error("No se pudieron obtener credenciales de SOLO LECTURA. No se puede construir el servicio de Sheets.")
        return None
    try:
        return build('sheets', 'v4', credentials=_CREDENTIALS_RO)
    except Exception as e:
        logger.error(f"Error al construir el servicio de Google Sheets (RO): {e}")
        return None

def get_spreadsheet_id() -> str:
    return _SPREADSHEET_ID