import logging

# Configuramos el nivel de traza a INFO y obtenemos el logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Creamos un gestor de log
log_file = '/var/log/vocento/pds.log'
handler = logging.FileHandler(log_file)
handler.setLevel(logging.INFO)
# Definimos el formato que tendra el handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# Agregamos el handler al logger
logger.addHandler(handler)
