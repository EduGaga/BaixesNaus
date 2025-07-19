# in_telegram/comandos/baixes_totals.py

import logging
import json
import os
import asyncio
from telegram.ext import ContextTypes

from in_telegram.g_sheets.g_autentificacion import get_sheets_service_ro, get_spreadsheet_id

logger = logging.getLogger(__name__)

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

async def _get_cell_value_baixes(sheet_name: str, cell_range: str) -> str:
    service = get_sheets_service_ro()
    spreadsheet_id = get_spreadsheet_id()

    if not service or not spreadsheet_id:
        logger.error("Servicio de Google Sheets (RO) o Spreadsheet ID no cargados. No se puede leer el valor de la celda.")
        return "Error de configuración"
    try:
        sheet = service.spreadsheets()

        range_name = f"'{sheet_name}'!{cell_range}"

        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])
        if values and values[0]:
            return values[0][0]
        return "0"

    except Exception as e:
        logger.error(f"Error al leer celda {cell_range} de la hoja {sheet_name}: {e}")
        return "Error al leer"


async def _mostrar_baixes_totals_async(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"Ejecutando lógica asíncrona para /mostrar_baixes_totals para el chat {chat_id}")

    if not VALID_NAVE_LETTERS:
        await context.bot.send_message(chat_id=chat_id, text="No se pudo cargar la lista de naves válidas. Contacta con el administrador.")
        return

    if not get_sheets_service_ro() or not get_spreadsheet_id():
        logger.error("Servicio de Google Sheets (RO) o Spreadsheet ID no disponibles para bajas totales.")
        await context.bot.send_message(chat_id=chat_id, text="Error interno: No se pudo conectar con Google Sheets para leer bajas totales. Contacta con el administrador.")
        return

    for nave_letter in VALID_NAVE_LETTERS:
        sheet_name = f"Nau {nave_letter}"

        cell_value = await _get_cell_value_baixes(sheet_name, "I2")

        mensaje_respuesta = f"El total de baixes en la {sheet_name} es de {cell_value}"
        await context.bot.send_message(chat_id=chat_id, text=mensaje_respuesta)
        await asyncio.sleep(0.1)


def mostrar_baixes_totals(chat_id: int, context: ContextTypes.DEFAULT_TYPE, main_loop: asyncio.AbstractEventLoop) -> None:
    logger.info(f"Comando /mostrar_baixes_totals recibido del chat {chat_id}.")
    asyncio.run_coroutine_threadsafe(
        _mostrar_baixes_totals_async(chat_id, context),
        main_loop
    )