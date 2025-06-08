"""
HTTP Server per ricevere richieste da n8n
e gestire l'API del bridge
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class BridgeRequestHandler(BaseHTTPRequestHandler):
    """Handler per le richieste HTTP del bridge"""
    
    def __init__(self, message_handler, config, *args, **kwargs):
        self.message_handler = message_handler
        self.config = config
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """Gestisce richieste POST per inviare messaggi Meshtastic"""
        try:
            print(f"🔔 Richiesta POST ricevuta da {self.client_address[0]}")
            
            # Verifica Content-Length
            content_length = int(self.headers.get('Content-Length', 0))
            if self.config.ENABLE_DEBUG:
                print(f"📏 Content-Length: {content_length}")
            
            # Leggi body della richiesta
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                if self.config.ENABLE_DEBUG:
                    print(f"📄 Dati ricevuti: {post_data}")
                
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    if self.config.ENABLE_DEBUG:
                        print(f"📋 JSON decodificato: {data}")
                except json.JSONDecodeError as e:
                    print(f"❌ Errore JSON: {e}")
                    self._send_error_response(400, "JSON malformato")
                    return
            else:
                print("⚠️ Richiesta POST senza body")
                data = {}
            
            # Gestisci formato n8n (array con oggetti)
            data = self._normalize_n8n_data(data)
            
            # Estrai parametri
            to_node = data.get('to', '') if isinstance(data, dict) else ''
            message = data.get('message', '') if isinstance(data, dict) else ''
            
            if self.config.ENABLE_DEBUG:
                print(f"👤 Destinatario: {to_node}")
                print(f"💬 Messaggio: {message}")
            
            # Valida parametri
            if not to_node or not message:
                error_msg = f"Parametri mancanti - to: '{to_node}', message: '{message}'"
                print(f"❌ {error_msg}")
                self._send_error_response(400, error_msg)
                return
            
            # Aggiungi messaggio alla coda
            success = self.message_handler.queue_message(to_node, message)
            
            if success:
                response = {
                    "status": "success", 
                    "message": "Messaggio aggiunto alla coda",
                    "queued_message": {"to": to_node, "text": message}
                }
                self._send_json_response(200, response)
                print("✅ Messaggio accodato con successo")
            else:
                self._send_error_response(500, "Errore durante accodamento messaggio")
                
        except Exception as e:
            print(f"❌ Errore nel gestore POST: {e}")
            if self.config.ENABLE_DEBUG:
                import traceback
                traceback.print_exc()
            self._send_error_response(500, f"Errore server: {str(e)}")
    
    def do_GET(self):
        """Gestisce richieste GET per status e test"""
        try:
            url_parts = urlparse(self.path)
            path = url_parts.path
            
            print(f"🔔 Richiesta GET: {path}")
            
            if path == "/" or path == "/status":
                # Status del bridge
                response = self._get_bridge_status()
                self._send_json_response(200, response)
                
            elif path == "/test":
                # Test del bridge
                response = {
                    "status": "ok", 
                    "message": "Bridge HTTP funzionante",
                    "timestamp": self._get_timestamp()
                }
                self._send_json_response(200, response)
                
            elif path == "/queue":
                # Status della coda
                queue_status = self.message_handler.get_queue_status()
                self._send_json_response(200, queue_status)
                
            else:
                # Endpoint non trovato
                self._send_error_response(404, f"Endpoint '{path}' non trovato")
                
        except Exception as e:
            print(f"❌ Errore nel gestore GET: {e}")
            self._send_error_response(500, f"Errore server: {str(e)}")
    
    def do_OPTIONS(self):
        """Gestisce preflight CORS"""
        self._send_cors_headers()
        self.send_response(200)
        self.end_headers()
    
    def _normalize_n8n_data(self, data):
        """Normalizza dati provenienti da n8n"""
        # n8n invia spesso array: [{"output": {...}}]
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
            if self.config.ENABLE_DEBUG:
                print(f"📦 Primo elemento array: {data}")
        
        # n8n può incapsulare in "output"
        if isinstance(data, dict) and 'output' in data:
            data = data['output']
            if self.config.ENABLE_DEBUG:
                print(f"📦 Contenuto 'output': {data}")
        
        return data
    
    def _get_bridge_status(self):
        """Ritorna status completo del bridge"""
        from serial_manager import SerialManager
        
        serial_manager = SerialManager.get_instance()
        queue_status = self.message_handler.get_queue_status()
        
        return {
            "status": "running",
            "timestamp": self._get_timestamp(),
            "config": {
                "webhook_url": self.config.WEBHOOK_URL,
                "http_port": self.config.HTTP_PORT,
                "serial_port": self.config.SERIAL_PORT
            },
            "serial": serial_manager.get_status() if serial_manager else {"connected": False},
            "queue": queue_status
        }
    
    def _get_timestamp(self):
        """Ritorna timestamp corrente"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _send_json_response(self, status_code, data):
        """Invia risposta JSON"""
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
        
        if self.config.ENABLE_DEBUG:
            print(f"📡 Risposta {status_code}: {response_json}")
    
    def _send_error_response(self, status_code, error_message):
        """Invia risposta di errore"""
        error_data = {
            "status": "error",
            "message": error_message,
            "timestamp": self._get_timestamp()
        }
        self._send_json_response(status_code, error_data)
    
    def _send_cors_headers(self):
        """Invia header CORS"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def log_message(self, format, *args):
        """Silenzia log standard del server HTTP"""
        if self.config.ENABLE_DEBUG:
            super().log_message(format, *args)

class HTTPBridgeServer:
    """Server HTTP principale per il bridge"""
    
    def __init__(self, config, message_handler):
        self.config = config
        self.message_handler = message_handler
        self.server = None
        self.server_thread = None
        self.running = False
    
    def start(self):
        """Avvia il server HTTP"""
        try:
            # Crea handler factory con parametri iniettati
            def handler_factory(*args, **kwargs):
                return BridgeRequestHandler(self.message_handler, self.config, *args, **kwargs)
            
            # Crea server HTTP
            self.server = HTTPServer(('0.0.0.0', self.config.HTTP_PORT), handler_factory)
            self.running = True
            
            print(f"🌐 Server HTTP avviato su:")
            print(f"   - http://localhost:{self.config.HTTP_PORT}")
            print(f"   - http://127.0.0.1:{self.config.HTTP_PORT}")
            
            # Avvia server
            self.server.serve_forever()
            
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"❌ Porta {self.config.HTTP_PORT} già in uso!")
                print(f"   Prova a cambiare porta o chiudi il processo che la sta usando")
            else:
                print(f"❌ Errore OS server HTTP: {e}")
        except Exception as e:
            print(f"❌ Errore server HTTP: {e}")
            if self.config.ENABLE_DEBUG:
                import traceback
                traceback.print_exc()
    
    def stop(self):
        """Ferma il server HTTP"""
        if self.server:
            print("🛑 Arresto server HTTP...")
            self.running = False
            self.server.shutdown()
            self.server.server_close()
            print("✅ Server HTTP arrestato")
    
    def is_running(self):
        """Verifica se il server è in esecuzione"""
        return self.running and self.server is not None