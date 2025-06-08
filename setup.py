#!/usr/bin/env python3
"""
Setup script per Meshtastic ↔ n8n Bridge
Automatizza l'installazione e configurazione iniziale
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

class BridgeSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.python_executable = sys.executable
        
    def run_setup(self):
        """Esegue setup completo"""
        print("🚀 Setup Meshtastic ↔ n8n Bridge")
        print("=" * 50)
        
        try:
            self.check_python_version()
            self.install_dependencies()
            self.setup_configuration()
            self.test_installation()
            self.show_next_steps()
            
        except Exception as e:
            print(f"❌ Errore durante setup: {e}")
            sys.exit(1)
    
    def check_python_version(self):
        """Verifica versione Python"""
        print("🐍 Controllo versione Python...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            raise Exception(f"Python 3.7+ richiesto. Versione attuale: {version.major}.{version.minor}")
        
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    
    def install_dependencies(self):
        """Installa dipendenze Python"""
        print("📦 Installazione dipendenze...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            raise Exception("File requirements.txt non trovato")
        
        try:
            # Aggiorna pip
            subprocess.run([self.python_executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Installa dipendenze
            subprocess.run([self.python_executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                         check=True, capture_output=True)
            
            print("✅ Dipendenze installate")
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Errore installazione dipendenze: {e}")
    
    def setup_configuration(self):
        """Configura file di configurazione"""
        print("⚙️ Configurazione iniziale...")
        
        env_example = self.project_root / ".env.example"
        env_file = self.project_root / ".env"
        
        # Copia .env.example se .env non esiste
        if env_example.exists() and not env_file.exists():
            shutil.copy2(env_example, env_file)
            print("✅ File .env creato da template")
        
        # Setup interattivo
        self.interactive_config()
    
    def interactive_config(self):
        """Configurazione interattiva"""
        print("\\n🔧 Configurazione interattiva:")
        print("(Premi Enter per usare il valore di default)")
        
        config = {}
        
        # Porta seriale
        default_port = "COM3" if platform.system() == "Windows" else "/dev/ttyUSB0"
        config['SERIAL_PORT'] = input(f"Porta seriale [{default_port}]: ").strip() or default_port
        
        # URL webhook
        default_webhook = "http://localhost:5678/webhook/meshtastic"
        config['WEBHOOK_URL'] = input(f"URL webhook n8n [{default_webhook}]: ").strip() or default_webhook
        
        # Porta HTTP
        default_http_port = "8888"
        config['HTTP_PORT'] = input(f"Porta server HTTP [{default_http_port}]: ").strip() or default_http_port
        
        # Debug
        debug_choice = input("Abilita debug dettagliato? [y/N]: ").strip().lower()
        config['ENABLE_DEBUG'] = "true" if debug_choice in ['y', 'yes'] else "false"
        
        # Salva configurazione
        self.save_config(config)
    
    def save_config(self, config):
        """Salva configurazione nel file .env"""
        env_file = self.project_root / ".env"
        
        try:
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Aggiorna valori
            for key, value in config.items():
                # Cerca linea esistente
                import re
                pattern = f"^{key}=.*$"
                replacement = f"{key}={value}"
                
                if re.search(pattern, content, re.MULTILINE):
                    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                else:
                    content += f"\\n{replacement}"
            
            with open(env_file, 'w') as f:
                f.write(content)
                
            print("✅ Configurazione salvata")
            
        except Exception as e:
            print(f"⚠️ Errore salvataggio configurazione: {e}")
    
    def test_installation(self):
        """Testa installazione"""
        print("🧪 Test installazione...")
        
        try:
            # Test import moduli
            import serial
            import requests
            print("✅ Moduli Python importati correttamente")
            
            # Test CLI Meshtastic
            result = subprocess.run(["meshtastic", "--help"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ CLI Meshtastic funzionante")
            else:
                print("⚠️ CLI Meshtastic non trovato - installalo con: pip install meshtastic")
                
        except ImportError as e:
            raise Exception(f"Modulo mancante: {e}")
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout test CLI Meshtastic")
        except FileNotFoundError:
            print("⚠️ CLI Meshtastic non trovato - installalo con: pip install meshtastic")
    
    def show_next_steps(self):
        """Mostra passi successivi"""
        print("\\n🎉 Setup completato!")
        print("=" * 50)
        print("📋 Passi successivi:")
        print("\\n1. 🔌 Collega il dispositivo Meshtastic via USB")
        print("2. 🌐 Configura n8n:")
        print(f"   - Importa workflow da: workflows/meshtastic-bot.json")
        print(f"   - Attiva il workflow")
        print("3. 🚀 Avvia il bridge:")
        print(f"   python src/meshtastic_bridge.py")
        print("\\n4. 🧪 Test:")
        print("   - Invia un messaggio 'ciao' al tuo dispositivo Meshtastic")
        print("   - Verifica che il bot risponda")
        print("\\n📚 Documentazione completa: README.md")
        print("🐛 Issues: https://github.com/yourusername/meshtastic-n8n-bridge/issues")

def main():
    """Funzione principale"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Meshtastic ↔ n8n Bridge Setup")
        print("\\nUso:")
        print("  python setup.py          # Setup completo")
        print("  python setup.py --help   # Mostra questo help")
        return
    
    setup = BridgeSetup()
    setup.run_setup()

if __name__ == "__main__":
    main()