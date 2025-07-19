# in_telegram/comandos/baixes_diaries.py

import logging
import asyncio
import json
import os
from telegram.ext import ContextTypes
from in_telegram.g_sheets.buscar_data_actual import buscar_data_actual_g_sheet
from in_telegram.utils.message_sender import send_message_sync_wrapper
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
            VALID_NAVE_LETTERS = [letter.upper() for letter in loaded_letters]
            logger.info(f"Naves válidas cargadas: {VALID_NAVE_LETTERS}")
        else:
            logger.error(f"El formato de '{NAVE_LIST_FILE_PATH}' es incorrecto. Debe ser una lista de cadenas de texto.")
except FileNotFoundError:
    logger.error(f"Archivo de lista de naves no encontrado en: {NAVE_LIST_FILE_PATH}. Asegúrate de que existe.")
except json.JSONDecodeError:
    logger.error(f"Error al decodificar JSON en: {NAVE_LIST_FILE_PATH}. Revisa el formato del archivo.")
except Exception as e:
    logger.error(f"Error inesperado al cargar la lista de naves desde {NAVE_LIST_FILE_PATH}: {e}")

async def _procesar_bajas_diarias_async(chat_id: int, context: ContextTypes.DEFAULT_TYPE, nave_seleccionada: str) -> str:
    logger.info(f"Procesando bajas diarias para Nau {nave_seleccionada} en chat {chat_id}")
    resultado_mensaje = ""

    try:
        fila_fecha_actual = await buscar_data_actual_g_sheet(nave_seleccionada)

        if fila_fecha_actual is None:
            error_msg = f"No sa torbat la data d'avui a la nau {nave_seleccionada}."
            await context.bot.send_message(chat_id=chat_id, text=error_msg)
            logger.error(f"Fila de fecha actual no encontrada para Nau {nave_seleccionada}.")
            return error_msg

        logger.info(f"Fecha actual encontrada en la fila: {fila_fecha_actual} para Nau {nave_seleccionada}.")

        service_ro = get_sheets_service_ro()
        spreadsheet_id = get_spreadsheet_id()
        if not service_ro or not spreadsheet_id:
            error_msg = "Error interno: No se pudo conectar con Google Sheets para leer bajas diarias."
            await context.bot.send_message(chat_id=chat_id, text=error_msg)
            return error_msg

        range_diario_bajas_sac = f"'Nau {nave_seleccionada}'!D{fila_fecha_actual}"
        range_diario_bajas_no_sac = f"'Nau {nave_seleccionada}'!E{fila_fecha_actual}"

        try:
            result_sac = service_ro.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_diario_bajas_sac
            ).execute()
            bajas_sac = result_sac.get('values', [['0']])[0][0]
        except Exception as e_sac:
            logger.error(f"Error al leer SAC para Nau {nave_seleccionada} en {range_diario_bajas_sac}: {e_sac}")
            bajas_sac = "Error"

        try:
            result_no_sac = service_ro.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_diario_bajas_no_sac
            ).execute()
            bajas_no_sac = result_no_sac.get('values', [['0']])[0][0]
        except Exception as e_no_sac:
            logger.error(f"Error al leer NO SAC para Nau {nave_seleccionada} en {range_diario_bajas_no_sac}: {e_no_sac}")
            bajas_no_sac = "Error"

        resultado_mensaje = f"Baixes del dia en la nau  {nave_seleccionada}:\nSAC: {bajas_sac}\nNO SAC: {bajas_no_sac}"
        await context.bot.send_message(chat_id=chat_id, text=resultado_mensaje)
        await asyncio.sleep(0.1) 

        return resultado_mensaje
    except Exception as e:
        logger.error(f"Error procesando bajas diarias para Nau {nave_seleccionada}: {e}")
        error_msg = f"Ha ocurrido un error al intentar procesar las bajas diarias para Nau {nave_seleccionada}."
        await context.bot.send_message(chat_id=chat_id, text=error_msg)
        return error_msg

def bajas_diarias_handler(chat_id: int, context: ContextTypes.DEFAULT_TYPE, main_loop: asyncio.AbstractEventLoop) -> None:
    logger.info(f"Comando de bajas diarias recibido del chat {chat_id}. Procesando todas las naves.")

    if not VALID_NAVE_LETTERS:
        send_message_sync_wrapper(chat_id, context, "No se pudo cargar la lista de naves válidas para bajas diarias. Contacta con el administrador.", main_loop)
        logger.error("No hay naves válidas para procesar en bajas diarias.")
        return

    all_results_messages = []

    for nave_letter in VALID_NAVE_LETTERS:
        future = asyncio.run_coroutine_threadsafe(
            _procesar_bajas_diarias_async(chat_id, context, nave_letter),
            main_loop
        )
        result_message = future.result()
        all_results_messages.append(result_message)
        
    
    final_telegram_message += "\n".join(all_results_messages)
    send_message_sync_wrapper(chat_id, context, final_telegram_message, main_loop)        
