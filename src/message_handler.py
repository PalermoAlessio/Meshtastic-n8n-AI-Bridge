"""
Message Handler per gestire l'invio e ricezione di messaggi
tra Meshtastic e n8n
"""

import json
import queue
import subprocess
import threading
import time
import requests
from datetime import datetime

class MessageHandler:
    """Gestisce l'invio e ricezione di messaggi"""
    
    def __init__(self, config):
        self.config = config
        self.message_queue = queue.Queue()
        self.queue_lock = threading.Lock()
        
    def send_to_n8n(self, message_data):
        """Invia messaggio a n8n tramite webhook"""
        try:
            response = requests.post(
                self.config.WEBHOOK_URL, 
                json=message_data, 
                timeout=self.config.HTTP_TIMEOUT
            )
            
            if response.status_code == 200:
                print(f"✅ Inviato a n8n: {message_data['text']}")
            else:
                print(f"❌ Errore n8n: HTTP {response.status_code}")
                if self.config.ENABLE_DEBUG:
                    print(f"   Risposta: {response.text}")
                    
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout connessione n8n ({self.config.HTTP_TIMEOUT}s)")
        except requests.exceptions.ConnectionError:
            print(f"❌ Errore connessione n8n: Impossibile raggiungere {self.config.WEBHOOK_URL}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Errore richiesta n8n: {e}")
        except Exception as e:
            print(f"❌ Errore generico invio n8n: {e}")
    
    def queue_message(self, to_node, message):
        """Aggiunge messaggio alla coda di invio"""
        try:
            self.message_queue.put({
                'to': to_node, 
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            print(f"📤 Messaggio aggiunto alla coda: {message} → {to_node}")
            return True
        except Exception as e:
            print(f"❌ Errore aggiunta coda: {e}")
            return False
    
    def process_queue(self):
        """Processa periodicamente la coda dei messaggi da inviare"""
        print("📦 Sistema coda messaggi avviato")
        
        while True:
            try:
                # Controlla se ci sono messaggi da inviare
                if not self.message_queue.empty():
                    # Raccogli tutti i messaggi nella coda
                    messages_to_send = []
                    while not self.message_queue.empty():
                        try:
                            msg = self.message_queue.get_nowait()
                            messages_to_send.append(msg)
                        except queue.Empty:
                            break
                    
                    if messages_to_send:
                        print(f"📦 Elaborazione {len(messages_to_send)} messaggi dalla coda...")
                        self._send_queued_messages(messages_to_send)
                
                # Aspetta prima del prossimo controllo
                time.sleep(self.config.QUEUE_PROCESS_INTERVAL)
                
            except Exception as e:
                print(f"❌ Errore nel processamento coda: {e}")
                time.sleep(5)  # Pausa più lunga in caso di errore
    
    def _send_queued_messages(self, messages):
        """Invia lista di messaggi utilizzando il CLI Meshtastic"""
        from serial_manager import SerialManager
        
        # Ottieni riferimento al serial manager (shared instance)
        serial_manager = SerialManager.get_instance()
        
        with self.queue_lock:
            # Chiudi temporaneamente connessione seriale
            if serial_manager:
                serial_manager.disconnect_for_cli()
            
            # Invia tutti i messaggi
            for msg in messages:
                success = self._send_message_via_cli(msg['to'], msg['message'])
                if success:
                    print(f"✅ Inviato: {msg['message']} → {msg['to']}")
                else:
                    print(f"❌ Fallito: {msg['message']} → {msg['to']}")
                time.sleep(self.config.MESSAGE_DELAY)
            
            # Riapri connessione seriale
            time.sleep(1)  # Pausa di sicurezza
            if serial_manager:
                serial_manager.reconnect_after_cli()
    
    def _send_message_via_cli(self, to_node, message):
        """Invia singolo messaggio tramite CLI Meshtastic"""
        try:
            # Converti formato indirizzo (0x433df694 → !433df694)
            if to_node.startswith('0x'):
                cli_address = '!' + to_node[2:]
            else:
                cli_address = to_node
            
            cmd = [
                "meshtastic", 
                "--port", self.config.SERIAL_PORT, 
                "--dest", cli_address, 
                "--sendtext", message
            ]
            
            if self.config.ENABLE_DEBUG:
                print(f"🚀 Comando CLI: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=self.config.CLI_TIMEOUT
            )
            
            if result.returncode == 0:
                if self.config.ENABLE_DEBUG:
                    print(f"📤 CLI output: {result.stdout}")
                return True
            else:
                print(f"❌ CLI errore: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ CLI timeout ({self.config.CLI_TIMEOUT}s)")
            return False
        except FileNotFoundError:
            print(f"❌ CLI non trovato: Assicurati che 'meshtastic' sia installato")
            return False
        except Exception as e:
            print(f"❌ CLI errore generico: {e}")
            return False
    
    def get_queue_status(self):
        """Ritorna statistiche sulla coda"""
        return {
            "queue_size": self.message_queue.qsize(),
            "queue_empty": self.message_queue.empty()
        }