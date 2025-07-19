# in_telegram/g_sheets/sheets.py

import logging
import asyncio
import re
import datetime 
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from in_telegram.utils.message_sender import send_message_sync_wrapper
from in_telegram.validadores.llista_naus_valides import llista_naus_valides 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRETS_DIR = os.path.abspath(os.path.join(BASE_DIR, '../../secrets'))

SPREADSHEET_ID = os.path.join(SECRETS_DIR, 's_sheets')
SERVICE_ACCOUNT_FILE = os.path.join(SECRETS_DIR, 'login.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets'] 
 
def _get_sheet_config(nave) -> tuple[str, str, str]:
    try:
        with open(SPREADSHEET_ID, 'r') as file:
            spreadsheet_id = file.read().strip()
            if not spreadsheet_id:
                raise ValueError("El archivo s_sheets está vacío.")
    except FileNotFoundError:
        logger.critical(f"Error crítico: Archivo SPREADSHEET_ID no encontrado en {SPREADSHEET_ID}")
        raise
    except Exception as e:
        logger.critical(f"Error al leer SPREADSHEET_ID de {SPREADSHEET_ID}: {e}")
        raise
    
    SHEET_NAME = f"Nau {nave}" #Hoja de calculo
    data_range = "B7:B101" #Rango de fechas

    logger.debug(f"Configuración de hoja cargada: ID='{spreadsheet_id}', Hoja='{SHEET_NAME}', Rango='{data_range}'")
    return spreadsheet_id, SHEET_NAME, data_range # Retornar las tres variables        

def _num_data(api_dates: list[list[str]], current_date_str: str) -> int | None:
    # Aplanar la lista de listas a una sola lista de strings para facilitar la búsqueda
    flattened_dates = [date_item for sublist in api_dates for date_item in sublist]
    
    #logger.info(f"Buscando '{current_date_str}' en las fechas de la API: {flattened_dates}")

    try:
        # Buscar la fecha actual en la lista aplanada
        # index() devuelve la primera posición de la coincidencia
        position_zero_based = flattened_dates.index(current_date_str)
        logger.info(f"Fecha '{current_date_str}' encontrada en la posición: {position_zero_based + 1}")
        return position_zero_based + 1
    except ValueError:
        # La fecha no se encontró en la lista
        logger.warning(f"La fecha '{current_date_str}' no se encontró en los datos de la API.")
        return None
    except Exception as e:
        logger.error(f"Error inesperado en _num_data al buscar la fecha: {e}")
        return None

def _escribir_Datos_sheets(spreadsheet_id: str, nombre_hoja: str, posicion_fecha: int, cantidad: int, sac_bool: bool, context, main_loop: asyncio.AbstractEventLoop,chat_id) -> None:
    try:
        target_row = posicion_fecha + 6 

        # Determinar la columna de destino
        if sac_bool:
            target_column = 'D' # Columna para SAC
        else:
            target_column = 'E' # Columna para NO SAC
        
        # Construir el rango de la celda específica
        cell_range = f"Nau {nombre_hoja}!{target_column}{target_row}"
        
        # Autenticación para escritura
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES # Usar el SCOPE de escritura
        )
        service = build('sheets', 'v4', credentials=creds)

        # obtener valor actual de la celda
        logger.info(f"Leyendo el valor actual de la celda: {cell_range}")
        result_read = service.spreadsheets().values().get(
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
                # --- ¡Aquí relanzamos una excepción personalizada! ---
                raise ValueError(f"Valor no numérico en la celda {cell_range}. No se puede sumar. Contenido: '{current_value_str}'") from ve
        else:
            logger.info(f"La celda {cell_range} está vacía. Se asumirá 0 para la suma.")

        new_total = current_value + cantidad
        logger.info(f"Nuevo total a escribir en {cell_range}: {new_total} (Actual: {current_value} + A sumar: {cantidad})")


        # Preparar el valor a escribir
        body = {
            'values': [[new_total]]
        }

        # Escribir el valor en la celda
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=cell_range,
            valueInputOption='RAW', # O 'USER_ENTERED' si quieres que Google Sheets interprete el valor
            body=body
        ).execute()

        logger.info(f"Datos escritos exitosamente: {result}")
        logger.info(f"Se escribió {cantidad} en la celda {cell_range}")

        message = f"Sa escrit de forma satisfactòria, el antic valor era {current_value} i el nou valor és {new_total}"
        asyncio.run_coroutine_threadsafe(
            send_message_sync_wrapper(chat_id, context, message),
            main_loop
        )
        
    except HttpError as err:
        error_details = err.error_details if hasattr(err, 'error_details') else str(err)
        logger.error(f"Error de la API de Google Sheets al intentar escribir: {err.resp.status} - {error_details}")
        raise # Relanzar la excepción para que g_sheets la capture y notifique al usuario
    except FileNotFoundError as err:
        logger.critical(f"Error crítico: Archivo de credenciales no encontrado para escritura: {err}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al intentar escribir los datos en Google Sheets: {e}")
        raise # Relanzar la excepción

def g_sheets(telegram_message_update: dict, context, main_loop: asyncio.AbstractEventLoop) -> None:

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

    if cantidad >= 1:
        try:

            if nave is None:
                error_msg = "Error: No se pudo extraer la letra de la nave del mensaje."
                logger.error(error_msg)
                asyncio.run_coroutine_threadsafe(
                    send_message_sync_wrapper(chat_id, context, error_msg),
                    main_loop
                )
                return

            if not llista_naus_valides(nave):
                error_msg = f"La nau {nave}, no està dins del rang de naus vàlides."
                logger.warning(error_msg)
                asyncio.run_coroutine_threadsafe(
                    send_message_sync_wrapper(chat_id, context, error_msg),
                    main_loop
                )
                return

            if cantidad is None:
                error_msg = "No s'ha pogut extreure la quantitat del missatge. Assegura't que el format sigui correcte."
                logger.error(error_msg)
                asyncio.run_coroutine_threadsafe(
                    send_message_sync_wrapper(chat_id, context, error_msg),
                    main_loop
                )
                return

            spreadsheet_id, sheet_name, data_range = _get_sheet_config(nave)
        
            # Autenticación con la cuenta de servicio
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            service = build('sheets', 'v4', credentials=creds)

            # Llamar a la API de Google Sheets
            # El rango se especifica como 'NombreDeHoja!Rango'
            range_to_read = f"{sheet_name}!{data_range}"
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_to_read
            ).execute()
        
            values = result.get('values', [])

            if not values:
                response_text = f"No s'han trobat les dades en el rang '{sheet_name}!'{data_range}' del full de càlcul."
                logger.error(response_text)
                asyncio.run_coroutine_threadsafe(
                    send_message_sync_wrapper(chat_id, context, response_text),
                    main_loop
                )
                return
            else:
                flattened_values = [item for sublist in values for item in sublist]
            
            posicion_fecha = None # Inicializar
            try:
                posicion_fecha = _num_data(values, fecha_actual)
                if posicion_fecha is None:
                    logger.error("La fecha actual no se encontró en los datos de la hoja de cálculo.")
                    asyncio.run_coroutine_threadsafe(
                        send_message_sync_wrapper(chat_id, context, f"La data actual '{fecha_actual}' no sa trobat dins de la fulla de càlcul"),
                        main_loop
                    )
                    return
               
                #Sescriuen les dades a la fulla de càlcul
                _escribir_Datos_sheets(spreadsheet_id, nave, posicion_fecha, cantidad, sac_bool, context, main_loop,chat_id)

            except Exception as e:
                logger.error(f"Error al llamar a _num_data: {e}")
                posicion_fecha = None # Asegurar que sea None si hay un error inesperado
                asyncio.run_coroutine_threadsafe(
                    send_message_sync_wrapper(chat_id, context, f"Hi ha hagut un error al processar la data actual: {e}"),
                    main_loop
                )
                return    


        except HttpError as err:
            error_message = f"Error de la API de Google Sheets: {err}"
            logger.error(error_message)
            asyncio.run_coroutine_threadsafe(
                send_message_sync_wrapper(chat_id, context, f"Hi ha hagut un error al accedir al full de dades"),
                main_loop
            )
            return
        except FileNotFoundError as err:
            error_message = f"Error: Archivo de credenciales o SPREADSHEET_ID no encontrado: {err}"
            logger.critical(error_message)
            asyncio.run_coroutine_threadsafe(
                send_message_sync_wrapper(chat_id, context, "Hi ha un error amb l'autentificació amb el full de dades."),
                main_loop
            )
            return
        except Exception as e:
            error_message = f"Error inesperado en g_sheets: {e}"
            logger.error(error_message)
            asyncio.run_coroutine_threadsafe(
                send_message_sync_wrapper(chat_id, context, f"Hi ha hagut un error inesperat amb la comunicació del full de dades."),
                main_loop
            )
            return
    else:        
        error = f"Sa entregat un valor de baixes igual o innferior a 0"
        logger.info(error)
        asyncio.run_coroutine_threadsafe(
            send_message_sync_wrapper(chat_id, context, f"El nombre de baixes ha de ser igual o superior a 1."),
            main_loop
        )
    pass