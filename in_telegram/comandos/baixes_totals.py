# in_telegram/comandos/baixes_totals.py

import logging
import json
import os
import asyncio
from telegram.ext import ContextTypes
from in_telegram.utils.message_sender import send_message_sync_wrapper
from googleapiclient.discovery import build
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

# Cargar la llista de naus válidas desde llista_naus.json
NAVE_LIST_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
    'in_telegram', 'utils', 'llista_naus.json'
)

VALID_NAVE_LETTERS = []
try:
    with open(NAVE_LIST_FILE_PATH, 'r', encoding='utf-8') as f:
        loaded_letters = json.load(f)
        if isinstance(loaded_letters, list) and all(isinstance(item, str) for item in loaded_letters):
            VALID_NAVE_LETTERS = [letter.upper() for letter in loaded_letters] # Convertir a mayúsculas al cargar
        else:
            logger.error(f"El formato de '{NAVE_LIST_FILE_PATH}' es incorrecto. Debe ser una lista de cadenas de texto.")
except FileNotFoundError:
    logger.error(f"Archivo de lista de naves no encontrado en: {NAVE_LIST_FILE_PATH}. Asegúrate de que existe.")
except json.JSONDecodeError:
    logger.error(f"Error al decodificar JSON en: {NAVE_LIST_FILE_PATH}. Revisa el formato del archivo.")
except Exception as e:
    logger.error(f"Error inesperado al cargar la lista de naves desde {NAVE_LIST_FILE_PATH}: {e}")


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'secrets', 's_sheets', 'sheets_service_account.json'
)
SPREADSHEET_ID_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'secrets', 's_sheets', 'spreadsheet_id.json'
)

creds = None
SPREADSHEET_ID = None

try:
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    with open(SPREADSHEET_ID_FILE, 'r', encoding='utf-8') as f:
        spreadsheet_config = json.load(f)
        SPREADSHEET_ID = spreadsheet_config.get('spreadsheet_id')
    if not SPREADSHEET_ID:
        logger.error(f"Spreadsheet ID no encontrado en {SPREADSHEET_ID_FILE}. Por favor, asegúrate de que el JSON contiene la clave 'spreadsheet_id'.")
except FileNotFoundError as e:
    logger.error(f"Error al cargar credenciales de Sheets o archivo de Spreadsheet ID para 'baixes_totals': {e}. Asegúrate de que 'sheets_service_account.json' y 'spreadsheet_id.json' están en 'secrets/s_sheets'.")
except json.JSONDecodeError:
    logger.error(f"Error al decodificar JSON desde el archivo de configuración de Sheets para 'baixes_totals'. Revisa el formato de '{SERVICE_ACCOUNT_FILE}' o '{SPREADSHEET_ID_FILE}'.")
except Exception as e:
    logger.error(f"Error inesperado al cargar la configuración de Google Sheets en 'baixes_totals': {e}")


async def _get_cell_value_baixes(sheet_name: str, cell_range: str) -> str:
    if not creds or not SPREADSHEET_ID:
        logger.error("Credenciales de Google Sheets o Spreadsheet ID no cargados en 'baixes_totals'. No se puede leer el valor de la celda.")
        return "Error de configuración"
    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        
        range_name = f"'{sheet_name}'!{cell_range}"
        
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if values and values[0]:
            return values[0][0]
        return "0"
        
    except Exception as e:
        logger.error(f"Error al leer celda {cell_range} de la hoja {sheet_name} en 'baixes_totals': {e}")
        return "Error al leer"


async def _mostrar_baixes_totals_async(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"Ejecutando lógica asíncrona para /mostrar_baixes_totals para el chat {chat_id}")

    if not VALID_NAVE_LETTERS:
        await context.bot.send_message(chat_id=chat_id, text="No se pudo cargar la lista de naves válidas. Contacta con el administrador.")
        return

    for nave_letter in VALID_NAVE_LETTERS:
        sheet_name = f"Nau {nave_letter}"
        
        cell_value = await _get_cell_value_baixes(sheet_name, "I2") 

        mensaje_respuesta = f"Bajas totales en {sheet_name}: {cell_value}"
        await context.bot.send_message(chat_id=chat_id, text=mensaje_respuesta)
        await asyncio.sleep(0.1)


def mostrar_baixes_totals(chat_id: int, context: ContextTypes.DEFAULT_TYPE, main_loop: asyncio.AbstractEventLoop) -> None:
    logger.info(f"Comando /mostrar_baixes_totals recibido del chat {chat_id}.")
    asyncio.run_coroutine_threadsafe(
        _mostrar_baixes_totals_async(chat_id, context),
        main_loop
    )