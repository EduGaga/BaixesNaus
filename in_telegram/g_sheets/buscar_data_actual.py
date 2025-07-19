# in_telegram/g_sheets/buscar_data_actual.py

import logging
import datetime
from in_telegram.g_sheets.g_autentificacion import get_sheets_service_ro, get_spreadsheet_id

logger = logging.getLogger(__name__)

def _num_data(api_dates: list[list[str]], current_date_str: str) -> int | None:
    flattened_dates = [date_item for sublist in api_dates for date_item in sublist]

    try:
        position_zero_based = flattened_dates.index(current_date_str)
        logger.info(f"Fecha '{current_date_str}' encontrada en la posición: {position_zero_based}")
        return position_zero_based + 6
    except ValueError:
        logger.warning(f"La fecha '{current_date_str}' no se encontró en los datos de la API.")
        return None
    except Exception as e:
        logger.error(f"Error inesperado en _num_data al buscar la fecha: {e}")
        return None

async def buscar_data_actual_g_sheet(nave_letter: str) -> int | None:
    service_ro = get_sheets_service_ro()
    spreadsheet_id = get_spreadsheet_id()

    if not service_ro or not spreadsheet_id:
        logger.error("Servicio de Google Sheets (RO) o Spreadsheet ID no disponibles. No se puede buscar la fecha actual.")
        return None

    fecha_actual = datetime.date.today().strftime("%d/%m/%y")
    logger.info(f"Buscando fecha actual: {fecha_actual} para Nau {nave_letter}")

    try:
        sheet_name_full = f"Nau {nave_letter}"
        data_range = "B7:B101" # Rango donde se encuentran las fechas
        range_to_read = f"'{sheet_name_full}'!{data_range}"

        logger.info(f"Intentando leer de '{spreadsheet_id}', rango '{range_to_read}'.")

        result = service_ro.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_to_read
        ).execute()

        values = result.get('values', [])

        if not values:
            logger.error(f"No se encontraron datos de fechas en el rango '{range_to_read}' del full de càlcul.")
            return None

        posicion_fecha = _num_data(values, fecha_actual)+1
        if posicion_fecha is None:
            logger.error(f"La fecha actual '{fecha_actual}' no se encontró en los datos de la hoja de cálculo para Nau {nave_letter}.")
            return None

        logger.info(f"Fecha actual '{fecha_actual}' encontrada en la fila {posicion_fecha} para Nau {nave_letter}.")
        return posicion_fecha

    except Exception as e:
        logger.error(f"Error inesperado en buscar_data_actual_g_sheet para Nau {nave_letter}: {e}")
        return None