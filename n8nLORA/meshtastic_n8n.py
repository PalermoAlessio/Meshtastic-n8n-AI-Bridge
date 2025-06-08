import serial
import re
import threading
import time
import requests
import json
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import queue

# Configurazione
WEBHOOK_URL = "http://localhost:5678/webhook/meshtastic"
HTTP_PORT = 8888

# Variabili globali
ser = None
port_name = ""
message_queue = queue.Queue()  # Coda per i messaggi da inviare
queue_lock = threading.Lock()

class SendMessageHandler(BaseHTTPRequestHandler):
    """Handler per ricevere richieste di invio messaggi da n8n"""
    
    def do_POST(self):
        try:
            print(f"🔔 Ricevuta richiesta HTTP da n8n")
            
            # Leggi il body della richiesta
            content_length = int(self.headers.get('Content-Length', 0))
            print(f"📏 Content-Length: {content_length}")
            
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                print(f"📄 Dati ricevuti: {post_data}")
                
                data = json.loads(post_data.decode('utf-8'))
                print(f"📋 JSON decodificato: {data}")
                print(f"🔍 Tipo dati: {type(data)}")
                
                # n8n invia un array, prendiamo il primo elemento
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                    print(f"📦 Primo elemento array: {data}")
                
                # n8n potrebbe incapsulare in "output"
                if isinstance(data, dict) and 'output' in data:
                    data = data['output']
                    print(f"📦 Contenuto 'output': {data}")
                    
            else:
                print("⚠️ Nessun body nella richiesta")
                data = {}
            
            # Estrai parametri
            to_node = data.get('to', '') if isinstance(data, dict) else ''
            message = data.get('message', '') if isinstance(data, dict) else ''
            
            print(f"👤 Destinatario: {to_node}")
            print(f"💬 Messaggio: {message}")
            
            if to_node and message:
                print(f"📤 Aggiunto alla coda...")
                # Aggiungi alla coda invece di inviare subito
                message_queue.put({'to': to_node, 'message': message})
                
                response = {"status": "success", "message": "Messaggio aggiunto alla coda"}
                self.send_response(200)
                print("✅ Risposta 200 inviata (messaggio in coda)")
            else:
                response = {"status": "error", "message": f"Parametri mancanti - to: {to_node}, message: {message}"}
                self.send_response(400)
                print("❌ Risposta 400 inviata (parametri mancanti)")
            
            # Invia risposta
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # CORS
            self.end_headers()
            
            response_json = json.dumps(response)
            self.wfile.write(response_json.encode())
            print(f"📡 Risposta inviata: {response_json}")
            
        except Exception as e:
            print(f"❌ ERRORE nel server HTTP: {e}")
            print(f"🔍 Tipo errore: {type(e)}")
            import traceback
            print(f"📍 Stack trace: {traceback.format_exc()}")
            
            try:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {"status": "error", "message": f"Errore server: {str(e)}"}
                self.wfile.write(json.dumps(error_response).encode())
            except:
                pass
    
    def do_GET(self):
        """Gestisci richieste GET per test"""
        print("🔔 Ricevuta richiesta GET (test)")
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        test_response = {"status": "ok", "message": "Server HTTP funzionante", "queue_size": message_queue.qsize()}
        self.wfile.write(json.dumps(test_response).encode())
    
    def log_message(self, format, *args):
        pass

def process_message_queue():
    """Processa periodicamente la coda dei messaggi da inviare"""
    global ser
    
    while True:
        try:
            # Controlla se ci sono messaggi da inviare
            if not message_queue.empty():
                # Raccogli tutti i messaggi nella coda
                messages_to_send = []
                while not message_queue.empty():
                    try:
                        msg = message_queue.get_nowait()
                        messages_to_send.append(msg)
                    except queue.Empty:
                        break
                
                if messages_to_send:
                    print(f"📦 Invio {len(messages_to_send)} messaggi dalla coda...")
                    
                    # Chiudi connessione seriale temporaneamente
                    with queue_lock:
                        if ser and ser.is_open:
                            ser.close()
                            print("🔌 Connessione seriale chiusa temporaneamente")
                        
                        # Invia tutti i messaggi
                        for msg in messages_to_send:
                            success = send_message_via_cli(msg['to'], msg['message'])
                            if success:
                                print(f"✅ Inviato: {msg['message']} → {msg['to']}")
                            else:
                                print(f"❌ Fallito: {msg['message']} → {msg['to']}")
                            time.sleep(0.5)  # Piccola pausa tra messaggi
                        
                        # Riapri connessione seriale
                        time.sleep(1)  # Pausa per essere sicuri
                        try:
                            ser = serial.Serial(port_name, 115200, timeout=1)
                            print("🔌 Connessione seriale riaperta")
                        except Exception as e:
                            print(f"❌ Errore riapertura seriale: {e}")
            
            time.sleep(2)  # Controlla la coda ogni 2 secondi
            
        except Exception as e:
            print(f"❌ Errore nel processamento coda: {e}")
            time.sleep(5)

def send_message_via_cli(to_node, message):
    """Invia singolo messaggio tramite CLI (connessione seriale chiusa)"""
    try:
        cmd = ["meshtastic", "--port", port_name, "--dest", to_node, "--sendtext", message]
        print(f"🚀 Comando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print(f"📤 CLI: Inviato con successo")
            return True
        else:
            print(f"❌ CLI: Errore - {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ CLI: Timeout")
        return False
    except Exception as e:
        print(f"❌ CLI: Errore - {e}")
        return False

def start_http_server():
    """Avvia server HTTP per ricevere richieste da n8n"""
    try:
        # Usa '0.0.0.0' per ascoltare su tutte le interfacce
        server = HTTPServer(('0.0.0.0', HTTP_PORT), SendMessageHandler)
        print(f"🌐 Server HTTP avviato su:")
        print(f"   - http://localhost:{HTTP_PORT}")
        print(f"   - http://127.0.0.1:{HTTP_PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Errore server HTTP: {e}")
        print(f"   Prova a cambiare porta (attualmente {HTTP_PORT})")
        print(f"   O verifica se la porta è già in uso")

def send_to_n8n(message_data):
    """Invia il messaggio a n8n tramite webhook"""
    try:
        response = requests.post(WEBHOOK_URL, json=message_data, timeout=5)
        if response.status_code == 200:
            print(f"✅ Inviato a n8n: {message_data['text']}")
        else:
            print(f"❌ Errore n8n: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore connessione n8n: {e}")
    except Exception as e:
        print(f"❌ Errore generico: {e}")

def extract_message_text(line):
    """Estrae il testo del messaggio dal log"""
    msg_match = re.search(r'msg=(.+)$', line)
    if msg_match:
        return msg_match.group(1).strip()
    return None

def main():
    global WEBHOOK_URL, port_name, ser
    
    port_name = input("Porta COM (es. COM3): ").strip()
    if not port_name:
        port_name = "COM3"
    
    webhook = input(f"URL webhook n8n (default: {WEBHOOK_URL}): ").strip()
    if webhook:
        WEBHOOK_URL = webhook
    
    print(f"🔌 Connessione a {port_name}...")
    print(f"🌐 Webhook n8n: {WEBHOOK_URL}")
    print(f"📡 Server HTTP: http://localhost:{HTTP_PORT}")
    print("👂 In ascolto per messaggi...")
    print("=" * 60)
    
    # Avvia server HTTP
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # Avvia processore coda messaggi
    queue_thread = threading.Thread(target=process_message_queue, daemon=True)
    queue_thread.start()
    print("📦 Sistema coda messaggi avviato")
    
    try:
        ser = serial.Serial(port_name, 115200, timeout=1)
        
        while True:
            # Usa il lock per evitare conflitti durante l'invio
            with queue_lock:
                if ser and ser.is_open:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                else:
                    line = ""
                    time.sleep(0.1)  # Aspetta se la connessione è chiusa
            
            if not line:
                continue
            
            if 'Received text msg' in line:
                ora = datetime.now().strftime("%H:%M:%S")
                
                from_match = re.search(r'from=(0x[a-f0-9]+)', line)
                id_match = re.search(r'id=(0x[a-f0-9]+)', line)
                text = extract_message_text(line)
                
                if text and from_match:
                    mittente = from_match.group(1)
                    message_id = id_match.group(1) if id_match else "Sconosciuto"
                    
                    print(f"💬 [{ora}] Da: {mittente}")
                    print(f"📝 Messaggio: {text}")
                    
                    message_data = {
                        "timestamp": ora,
                        "from": mittente,
                        "message_id": message_id,
                        "text": text,
                        "raw_timestamp": int(time.time())
                    }
                    
                    webhook_thread = threading.Thread(target=send_to_n8n, args=(message_data,))
                    webhook_thread.start()
                    
                    print("-" * 60)
                
    except serial.SerialException as e:
        print(f"❌ Errore seriale: {e}")
    except KeyboardInterrupt:
        print("\n👋 Uscita")
    finally:
        if ser and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()