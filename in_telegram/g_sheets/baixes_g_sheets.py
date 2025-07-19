# in_telegram/g_sheets/sheets.py

import logging
import asyncio
import re
import datetime 
import os
from googleapiclient.errors import HttpError
from in_telegram.validadores.llista_naus_valides import llista_naus_valides 
from in_telegram.g_sheets.g_autentificacion import get_sheets_service_ro, get_sheets_service_rw, get_spreadsheet_id
from in_telegram.g_sheets.buscar_data_actual import buscar_data_actual_g_sheet

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def _escribir_Datos_sheets(nave: str, posicion_fecha: int, cantidad: int, sac_bool: bool, context,chat_id) -> None:  
    try:
        service_rw = get_sheets_service_rw()
        service_ro = get_sheets_service_ro() # También necesitamos RO para leer el valor actual
        spreadsheet_id = get_spreadsheet_id()

        if not service_rw or not service_ro or not spreadsheet_id:
            logger.error("Servicio de Google Sheets (RW/RO) o Spreadsheet ID no disponibles. No se puede escribir.")
            await context.bot.send_message(chat_id=chat_id, text="Error interno: No se pudo conectar con Google Sheets para escribir. Contacta con el administrador.")
            return
    
        target_row = posicion_fecha

        # Determinar la columna de destino
        if sac_bool:
            target_column = 'D' # Columna para SAC
        else:
            target_column = 'E' # Columna para NO SAC
        
        sheet_name_full = f"Nau {nave}"
        cell_range = f"'{sheet_name_full}'!{target_column}{target_row}"
        
        logger.info(f"Leyendo el valor actual de la celda: {cell_range}")
        result_read = service_ro.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=cell_range,
            valueRenderOption='UNFORMATTED_VALUE' #Importante para obtener el valor numérico sin formato
        ).execute()

        current_value = 0

        if 'values' in result_read and result_read['values']:
            try:
                # La API devuelve lista de listas, si hay un valor, será [[valor]]
                current_value_str = str(result_read['values'][0][0]).strip()
                if current_value_str: # Solo intenta convertir si no está vacío
                    current_value = int(float(current_value_str)) # Convertir a float primero para manejar posibles decimales o enteros grandes, luego a int
                logger.info(f"Valor actual leído de {cell_range}: '{current_value_str}' (convertido a {current_value})")
            except ValueError as ve:
                logger.warning(f"La celda {cell_range} contiene un valor no numérico '{current_value_str}'. Se asumirá 0 para la suma. Error: {ve}")
                await context.bot.send_message(chat_id=chat_id, text=f"Error: La celda de la fulla de càlcul '{cell_range}' conté un valor no numèric. No es pot sumar.")
                return
            
        else:
            logger.info(f"La celda {cell_range} está vacía. Se asumirá 0 para la suma.")

        new_total = current_value + cantidad
        logger.info(f"Nuevo total a escribir en {cell_range}: {new_total} (Actual: {current_value} + A sumar: {cantidad})")


        # Preparar el valor a escribir
        body = {
            'values': [[new_total]]
        }

        # Escribir el valor en la celda
        result = service_rw.spreadsheets().values().update( 
            spreadsheetId=spreadsheet_id,
            range=cell_range,
            valueInputOption='RAW',
            body=body
        ).execute()

        logger.info(f"Datos escritos exitosamente: {result}")
        logger.info(f"Se escribió {cantidad} en la celda {cell_range}")

        message = f"Sa escrit de forma satisfactòria, el antic valor era {current_value} i el nou valor és {new_total}"
        await context.bot.send_message(chat_id=chat_id, text=message)
        
    except HttpError as err:
        error_details = err.error_details if hasattr(err, 'error_details') else str(err)
        logger.error(f"Error de la API de Google Sheets al intentar escribir: {err.resp.status} - {error_details}")
        await context.bot.send_message(chat_id=chat_id, text=f"Hi ha hagut un error amb la comunicació del full de dades: {err.resp.status}")
    except FileNotFoundError as err:
        logger.critical(f"Error crítico: Archivo de credenciales no encontrado para escritura: {err}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al intentar escribir los datos en Google Sheets: {e}")
        await context.bot.send_message(chat_id=chat_id, text=f"Hi ha hagut un error inesperat al intentar escriure les dades.")

async def g_sheets(telegram_message_update: dict, context, main_loop: asyncio.AbstractEventLoop) -> None:
    user_id = telegram_message_update.get('effective_user', {}).get('id', 'N/A')
    chat_id = telegram_message_update.get('message', {}).get('chat', {}).get('id')
    message_content = telegram_message_update.get('message', {}).get('text')

    #Extraer la fecha actual en formato "dd/mm/yy" 
    # Usamos datetime para obtener la fecha de hoy
    fecha_actual = datetime.date.today().strftime("%d/%m/%y")
    logger.info(f"Fecha actual extraída: {fecha_actual}")

    #Determinar si 'sac' está presente (sac_bool)
    # Convertimos el mensaje a minúsculas para una comparación sin distinción de mayúsculas
    processed_message = message_content.lower()
    sac_bool = "sac" in processed_message
    logger.info(f"'sac' presente en el mensaje: {sac_bool}")

    #Extraer cantidad (el número) y nave (la letra)
    message_for_extraction = processed_message.replace("sac", "").strip()
    message_for_extraction = re.sub(r'\s+', '', message_for_extraction)

    cantidad = None
    nave = None

    match = re.search(r'([a-zñç])(\d+)|(\d+)([a-zñç])', message_for_extraction, re.UNICODE)

    if match:
        if match.group(1): # Coincide con el patrón de letra-número (ej. "a1")
            nave = match.group(1).upper()
            cantidad = int(match.group(2))
        elif match.group(3): # Coincide con el patrón de número-letra (ej. "1a")
            cantidad = int(match.group(3))
            nave = match.group(4).upper() 
    
    logger.info(f"Cantidad extraída: {cantidad}")
    logger.info(f"Nave extraída: {nave}")

    if cantidad is None or cantidad < 1:
        error_msg = "El nombre de baixes ha de ser igual o superior a 1 i el format ha de ser correcte (ex: 'A10' o '10A')."
        logger.info(error_msg)
        await context.bot.send_message(chat_id=chat_id, text=error_msg)
        return

    if nave is None:
        error_msg = "Error: No se pudo extraer la letra de la nave del mensaje. Assegura't que el format sigui correcte."
        logger.error(error_msg)
        await context.bot.send_message(chat_id=chat_id, text=error_msg)
        return

    if not llista_naus_valides(nave):
        error_msg = f"La nau {nave} no està dins del rang de naus vàlides (A o B)."
        logger.warning(error_msg)
        await context.bot.send_message(chat_id=chat_id, text=error_msg)
        return

    try:
        # Definir el rango de fechas para leer (ahora sin _get_sheet_config)
        posicion_fecha = await buscar_data_actual_g_sheet(nave)
        if posicion_fecha is None:
            logger.error(f"La fecha actual '{fecha_actual}' no se encontró en los datos de la hoja de cálculo para Nau {nave}.")
            await context.bot.send_message(chat_id=chat_id, text=f"La data actual '{fecha_actual}' no s'ha trobat dins de la fulla de càlcul.")
            return
        
        await _escribir_Datos_sheets(nave, posicion_fecha, cantidad, sac_bool, context, chat_id)

    except HttpError as err:
        error_message = f"Error de la API de Google Sheets: {err.resp.status} - {err.error_details if hasattr(err, 'error_details') else str(err)}"
        logger.error(error_message)
        await context.bot.send_message(chat_id=chat_id, text=f"Hi ha hagut un error al accedir al full de dades: {err.resp.status}")
    except Exception as e:
        error_message = f"Error inesperado en g_sheets: {e}"
        logger.error(error_message)
        await context.bot.send_message(chat_id=chat_id, text=f"Hi ha hagut un error inesperat amb la comunicació del full de dades.")