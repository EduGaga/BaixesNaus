# in_telegram/validadores/llista_naus_valides.py

import logging
import json
import os

logger = logging.getLogger(__name__)

NAVE_LIST_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    'utils','llista_naus.json'
)

try:
    with open(NAVE_LIST_FILE_PATH, 'r', encoding='utf-8') as f:
        VALID_NAVE_LETTERS = json.load(f) 
    
    if not isinstance(VALID_NAVE_LETTERS, list) or not all(isinstance(item, str) for item in VALID_NAVE_LETTERS):
        logger.error(f"El formato de '{NAVE_LIST_FILE_PATH}' es incorrecto. Debe ser una lista de cadenas de texto. Usando lista vacía.")
        VALID_NAVE_LETTERS = []
    else:
        VALID_NAVE_LETTERS = [letter.upper() for letter in VALID_NAVE_LETTERS]

except FileNotFoundError:
    logger.error(f"Archivo de lista de naves no encontrado en: {NAVE_LIST_FILE_PATH}. Asegúrate de que existe.")
    VALID_NAVE_LETTERS = [] 
except json.JSONDecodeError:
    logger.error(f"Error al decodificar JSON en: {NAVE_LIST_FILE_PATH}. Revisa el formato del archivo.")
    VALID_NAVE_LETTERS = []
except Exception as e:
    logger.error(f"Error inesperado al cargar la lista de naves desde {NAVE_LIST_FILE_PATH}: {e}")
    VALID_NAVE_LETTERS = []


def llista_naus_valides(nave: str) -> bool:
    nave_mayusculas = nave.upper()

    if nave_mayusculas in VALID_NAVE_LETTERS:
        logger.info(f"Nave '{nave_mayusculas}' es válida.")
        return True
    else:
        logger.warning(f"Nave '{nave_mayusculas}' no está en la lista de naus vàlides: {VALID_NAVE_LETTERS}.")
        return False