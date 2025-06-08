"""
Serial Manager per gestire la connessione seriale
con dispositivi Meshtastic
"""

import serial
import time
import threading

class SerialManager:
    """Gestisce la connessione seriale con dispositivo Meshtastic"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self, config):
        self.config = config
        self.serial_connection = None
        self.connected = False
        self.read_lock = threading.Lock()
        
        # Imposta istanza singleton per accesso globale
        SerialManager._instance = self
    
    @classmethod
    def get_instance(cls):
        """Ritorna l'istanza singleton del SerialManager"""
        return cls._instance
    
    def connect(self):
        """Stabilisce connessione seriale"""
        try:
            print(f"🔌 Connessione a {self.config.SERIAL_PORT} @ {self.config.SERIAL_BAUDRATE} baud...")
            
            self.serial_connection = serial.Serial(
                port=self.config.SERIAL_PORT,
                baudrate=self.config.SERIAL_BAUDRATE,
                timeout=self.config.SERIAL_TIMEOUT
            )
            
            if self.serial_connection.is_open:
                self.connected = True
                print(f"✅ Connessione seriale stabilita")
                return True
            else:
                print(f"❌ Impossibile aprire porta seriale")
                return False
                
        except serial.SerialException as e:
            print(f"❌ Errore seriale: {e}")
            print(f"   Verifica che la porta {self.config.SERIAL_PORT} sia disponibile")
            print(f"   e che nessun altro programma la stia utilizzando")
            self.connected = False
            return False
        except Exception as e:
            print(f"❌ Errore generico connessione: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Chiude connessione seriale"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                print("🔌 Connessione seriale chiusa")
            self.connected = False
        except Exception as e:
            print(f"❌ Errore chiusura seriale: {e}")
    
    def disconnect_for_cli(self):
        """Disconnette temporaneamente per permettere uso CLI"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("🔌 Connessione seriale chiusa temporaneamente per CLI")
    
    def reconnect_after_cli(self):
        """Riconnette dopo uso CLI"""
        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                self.serial_connection = serial.Serial(
                    port=self.config.SERIAL_PORT,
                    baudrate=self.config.SERIAL_BAUDRATE,
                    timeout=self.config.SERIAL_TIMEOUT
                )
                if self.serial_connection.is_open:
                    print("🔌 Connessione seriale riaperta dopo CLI")
                    return True
        except Exception as e:
            print(f"❌ Errore riapertura seriale: {e}")
            return False
    
    def read_line(self):
        """Legge una linea dalla connessione seriale"""
        with self.read_lock:
            try:
                if not self.serial_connection or not self.serial_connection.is_open:
                    time.sleep(0.1)  # Aspetta se connessione chiusa
                    return ""
                
                line = self.serial_connection.readline()
                if line:
                    decoded_line = line.decode('utf-8', errors='ignore').strip()
                    if self.config.ENABLE_DEBUG and decoded_line:
                        # Mostra solo linee che contengono messaggi importanti
                        if any(keyword in decoded_line for keyword in ['Received', 'ERROR', 'WARNING']):
                            print(f"🔍 Serial: {decoded_line}")
                    return decoded_line
                return ""
                
            except serial.SerialException as e:
                if self.config.ENABLE_DEBUG:
                    print(f"❌ Errore lettura seriale: {e}")
                time.sleep(0.1)
                return ""
            except Exception as e:
                if self.config.ENABLE_DEBUG:
                    print(f"❌ Errore generico lettura: {e}")
                time.sleep(0.1)
                return ""
    
    def is_connected(self):
        """Verifica se la connessione è attiva"""
        try:
            return (self.serial_connection and 
                   self.serial_connection.is_open and 
                   self.connected)
        except:
            return False
    
    def get_status(self):
        """Ritorna stato della connessione seriale"""
        return {
            "connected": self.is_connected(),
            "port": self.config.SERIAL_PORT,
            "baudrate": self.config.SERIAL_BAUDRATE,
            "timeout": self.config.SERIAL_TIMEOUT
        }
    
    def flush_buffers(self):
        """Svuota i buffer di input e output"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()
                if self.config.ENABLE_DEBUG:
                    print("🧹 Buffer seriali svuotati")
        except Exception as e:
            print(f"❌ Errore svuotamento buffer: {e}")
    
    def test_connection(self):
        """Testa la connessione seriale"""
        try:
            if not self.is_connected():
                print("❌ Test fallito: Nessuna connessione")
                return False
            
            # Prova a leggere per qualche secondo per verificare che arrivino dati
            print("🔍 Test connessione in corso...")
            start_time = time.time()
            lines_received = 0
            
            while time.time() - start_time < 5:  # Test per 5 secondi
                line = self.read_line()
                if line:
                    lines_received += 1
                time.sleep(0.1)
            
            if lines_received > 0:
                print(f"✅ Test OK: {lines_received} linee ricevute in 5 secondi")
                return True
            else:
                print("⚠️ Test dubbioso: Nessun dato ricevuto in 5 secondi")
                print("   Verifica che il dispositivo Meshtastic sia acceso e configurato")
                return False
                
        except Exception as e:
            print(f"❌ Errore durante test: {e}")
            return False