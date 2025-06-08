"""
Configurazione per Meshtastic-n8n Bridge
"""
import os
from dotenv import load_dotenv

# Carica variabili d'ambiente da .env se presente
load_dotenv()

# Configurazione di default
DEFAULT_WEBHOOK_URL = "http://localhost:5678/webhook/meshtastic"
DEFAULT_HTTP_PORT = 8888
DEFAULT_SERIAL_PORT = "COM3"  # Windows default, su Linux sarà /dev/ttyUSB0
DEFAULT_BAUDRATE = 115200

# Configurazione caricata da environment o default
class Config:
    # URLs e porte
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', DEFAULT_WEBHOOK_URL)
    HTTP_PORT = int(os.getenv('HTTP_PORT', DEFAULT_HTTP_PORT))
    
    # Configurazione seriale
    SERIAL_PORT = os.getenv('SERIAL_PORT', DEFAULT_SERIAL_PORT)
    SERIAL_BAUDRATE = int(os.getenv('SERIAL_BAUDRATE', DEFAULT_BAUDRATE))
    SERIAL_TIMEOUT = int(os.getenv('SERIAL_TIMEOUT', 1))
    
    # Timing e performance
    QUEUE_PROCESS_INTERVAL = float(os.getenv('QUEUE_PROCESS_INTERVAL', 2.0))
    HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', 5))
    CLI_TIMEOUT = int(os.getenv('CLI_TIMEOUT', 15))
    MESSAGE_DELAY = float(os.getenv('MESSAGE_DELAY', 0.5))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    ENABLE_DEBUG = os.getenv('ENABLE_DEBUG', 'False').lower() == 'true'
    
    # Sicurezza
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '0.0.0.0,localhost,127.0.0.1').split(',')
    
    @classmethod
    def display_config(cls):
        """Mostra la configurazione attuale"""
        print("📋 Configurazione attuale:")
        print(f"   🌐 Webhook URL: {cls.WEBHOOK_URL}")
        print(f"   🔌 Porta seriale: {cls.SERIAL_PORT} @ {cls.SERIAL_BAUDRATE} baud")
        print(f"   📡 Server HTTP: http://localhost:{cls.HTTP_PORT}")
        print(f"   ⏱️  Intervallo coda: {cls.QUEUE_PROCESS_INTERVAL}s")
        print(f"   🐛 Debug: {'Abilitato' if cls.ENABLE_DEBUG else 'Disabilitato'}")
        print("=" * 60)