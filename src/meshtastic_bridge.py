#!/usr/bin/env python3
"""
Meshtastic ↔ n8n Bridge
Main bridge server per integrare dispositivi Meshtastic con n8n

Author: Il tuo nome
License: MIT
"""

import sys
import threading
import time
from datetime import datetime

from config import Config
from message_handler import MessageHandler
from serial_manager import SerialManager
from http_server import HTTPBridgeServer

class MeshtasticBridge:
    """Bridge principale tra Meshtastic e n8n"""
    
    def __init__(self):
        self.config = Config()
        self.serial_manager = SerialManager(self.config)
        self.message_handler = MessageHandler(self.config)
        self.http_server = HTTPBridgeServer(self.config, self.message_handler)
        
        # Thread management
        self.running = False
        self.threads = []
    
    def start(self):
        """Avvia tutti i componenti del bridge"""
        print("🚀 Avvio Meshtastic ↔ n8n Bridge")
        Config.display_config()
        
        try:
            # Avvia server HTTP
            print("🌐 Avvio server HTTP...")
            http_thread = threading.Thread(target=self.http_server.start, daemon=True)
            http_thread.start()
            self.threads.append(http_thread)
            
            # Avvia processore coda messaggi
            print("📦 Avvio sistema coda messaggi...")
            queue_thread = threading.Thread(target=self.message_handler.process_queue, daemon=True)
            queue_thread.start()
            self.threads.append(queue_thread)
            
            # Avvia monitoraggio seriale
            print("👂 Avvio monitoraggio messaggi Meshtastic...")
            self.running = True
            self.serial_manager.connect()
            
            # Main loop - lettura messaggi seriali
            self._main_loop()
            
        except KeyboardInterrupt:
            print("\n👋 Uscita richiesta dall'utente")
        except Exception as e:
            print(f"❌ Errore critico: {e}")
            if Config.ENABLE_DEBUG:
                import traceback
                traceback.print_exc()
        finally:
            self.stop()
    
    def _main_loop(self):
        """Loop principale per la lettura dei messaggi seriali"""
        print("✅ Bridge avviato! In ascolto per messaggi...")
        print("   Premi Ctrl+C per uscire")
        print("-" * 60)
        
        while self.running:
            try:
                # Leggi messaggio dalla connessione seriale
                line = self.serial_manager.read_line()
                
                if line and 'Received text msg' in line:
                    # Processa messaggio ricevuto
                    message_data = self._parse_meshtastic_message(line)
                    if message_data:
                        self._handle_incoming_message(message_data)
                        
            except Exception as e:
                print(f"❌ Errore nel loop principale: {e}")
                if Config.ENABLE_DEBUG:
                    import traceback
                    traceback.print_exc()
                time.sleep(1)  # Pausa in caso di errore
    
    def _parse_meshtastic_message(self, line):
        """Estrae dati dal messaggio Meshtastic"""
        import re
        
        try:
            # Estrai mittente
            from_match = re.search(r'from=(0x[a-f0-9]+)', line)
            if not from_match:
                return None
            
            # Estrai ID messaggio
            id_match = re.search(r'id=(0x[a-f0-9]+)', line)
            
            # Estrai testo messaggio
            text_match = re.search(r'msg=(.+)$', line)
            if not text_match:
                return None
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            message_data = {
                "timestamp": timestamp,
                "from": from_match.group(1),
                "message_id": id_match.group(1) if id_match else "unknown",
                "text": text_match.group(1).strip(),
                "raw_timestamp": int(time.time())
            }
            
            return message_data
            
        except Exception as e:
            print(f"❌ Errore parsing messaggio: {e}")
            return None
    
    def _handle_incoming_message(self, message_data):
        """Gestisce messaggio Meshtastic ricevuto"""
        print(f"💬 [{message_data['timestamp']}] Da: {message_data['from']}")
        print(f"📝 Messaggio: {message_data['text']}")
        
        # Invia a n8n in thread separato
        webhook_thread = threading.Thread(
            target=self.message_handler.send_to_n8n, 
            args=(message_data,)
        )
        webhook_thread.start()
        
        print("-" * 60)
    
    def stop(self):
        """Ferma tutti i componenti"""
        print("🛑 Arresto bridge...")
        self.running = False
        
        # Chiudi connessione seriale
        self.serial_manager.disconnect()
        
        # Ferma server HTTP
        self.http_server.stop()
        
        print("✅ Bridge arrestato")

def setup_interactive():
    """Setup interattivo per configurazione iniziale"""
    print("🔧 Setup Meshtastic ↔ n8n Bridge")
    print("=" * 40)
    
    # Richiedi porta seriale
    default_port = Config.SERIAL_PORT
    port = input(f"Porta seriale [{default_port}]: ").strip()
    if port:
        Config.SERIAL_PORT = port
    
    # Richiedi webhook URL
    default_webhook = Config.WEBHOOK_URL
    webhook = input(f"URL webhook n8n [{default_webhook}]: ").strip()
    if webhook:
        Config.WEBHOOK_URL = webhook
    
    # Richiedi porta HTTP
    default_http_port = Config.HTTP_PORT
    http_port = input(f"Porta server HTTP [{default_http_port}]: ").strip()
    if http_port and http_port.isdigit():
        Config.HTTP_PORT = int(http_port)
    
    print()

def main():
    """Funzione principale"""
    print("📡 Meshtastic ↔ n8n Bridge v1.0")
    print("=" * 40)
    
    # Setup interattivo se richiesto
    if len(sys.argv) > 1 and sys.argv[1] == '--setup':
        setup_interactive()
    
    # Avvia bridge
    bridge = MeshtasticBridge()
    bridge.start()

if __name__ == "__main__":
    main()