import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from in_telegram.verificar_uuid import es_usuario_autorizado
from in_telegram.validar_tipo_mensaje import es_mensaje_de_texto
from in_telegram.filtrar_mensajes import filtrar
from in_telegram.utils.message_sender import send_message_sync_wrapper 
import threading
import os
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Configuración
TELEGRAM_TOKEN_FILE = 'secrets/telegram'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  
    main_loop_for_thread = asyncio.get_running_loop() 
    
    thread = threading.Thread(
        target=process_message_in_thread,
        args=(update, context, main_loop_for_thread),
        daemon=True
    )
    thread.start()

def process_message_in_thread(update: Update, context: ContextTypes.DEFAULT_TYPE, current_loop: asyncio.AbstractEventLoop):
    """Función que se ejecuta en el hilo secundario para procesar todo el mensaje"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
        
    try:
        update_dict = update.to_dict()
        logger.info(f"Procesando mensaje del usuario {user_id} en hilo secundario")
        
        is_authorized = es_usuario_autorizado(update_dict)
        
        if not isinstance(is_authorized, bool):
            logger.error(f"Valor inesperado de es_usuario_autorizado: {is_authorized}")
            return
             
        if is_authorized:
            logger.info(f"Usuario {user_id} autorizado.")
            if not es_mensaje_de_texto(update_dict):
                logger.info(f"Mensaje del usuario {user_id}. No es un mensaje de texto.")
                asyncio.run_coroutine_threadsafe(
                    send_message_sync_wrapper(
                        chat_id=chat_id,
                        context=context,
                        message_text="Només s'admeten missatges de text."
                    ),
                    current_loop
                )
                return
            else:
                filtrar(update_dict, context, current_loop)
                return            
        else:
            logger.info(f"Usuario {user_id} no autorizado")
            return            
    
    except Exception as e:
        logger.error(f"Error en hilo secundario: {e}")

def get_telegram_token(file_path):
    """Lee el token de Telegram de un archivo"""
    if not os.path.exists(file_path):
        logger.error(f"Error: El archivo de token no se encontró en '{file_path}'.")
        raise FileNotFoundError(f"Archivo de token no encontrado: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            token = f.read().strip()
            if (token.startswith('"') and token.endswith('"')) or \
               (token.startswith("'") and token.endswith("'")):
                token = token[1:-1]
            
            if not token:
                logger.error(f"Error: El archivo '{file_path}' está vacío.")
                raise ValueError("Token vacío")
            return token
    except Exception as e:
        logger.error(f"Error al leer el token: {e}")
        raise

def main() -> None:
    try:
        telegram_token = get_telegram_token(TELEGRAM_TOKEN_FILE)

        application = Application.builder().token(telegram_token).build()

        application.add_handler(MessageHandler(filters.ALL, handle_message))

        logger.warning("El bot se ha iniciado correctamente y está a la espera de recibir mensajes...")
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"Error fatal: {e}")
        exit(1)

if __name__ == '__main__':
    main()