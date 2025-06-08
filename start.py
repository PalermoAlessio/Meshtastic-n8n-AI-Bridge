#!/usr/bin/env python3
"""
Script di avvio semplificato per Meshtastic ↔ n8n Bridge
Gestisce setup automatico e avvio del bridge
"""

import sys
import os
from pathlib import Path

# Aggiungi src al path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def check_setup():
    """Verifica se il setup è stato completato"""
    try:
        # Verifica file di configurazione
        env_file = project_root / ".env"
        if not env_file.exists():
            print("⚠️ File .env non trovato")
            return False
        
        # Verifica dipendenze
        import serial
        import requests
        
        return True
        
    except ImportError as e:
        print(f"❌ Dipendenza mancante: {e}")
        return False

def run_setup():
    """Esegue setup se necessario"""
    print("🔧 Setup necessario. Avvio setup automatico...")
    try:
        from setup import BridgeSetup
        setup = BridgeSetup()
        setup.run_setup()
        return True
    except Exception as e:
        print(f"❌ Errore durante setup: {e}")
        return False

def main():
    """Funzione principale"""
    print("📡 Meshtastic ↔ n8n Bridge")
    print("=" * 40)
    
    # Controlla argomenti
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ["--help", "-h"]:
            print("Uso:")
            print("  python start.py          # Avvia bridge")
            print("  python start.py --setup  # Forza setup")
            print("  python start.py --test   # Test configurazione")
            print("  python start.py --help   # Mostra questo help")
            return
            
        elif arg == "--setup":
            if run_setup():
                print("\\n✅ Setup completato. Riavvia con: python start.py")
            return
            
        elif arg == "--test":
            print("🧪 Test configurazione...")
            if check_setup():
                print("✅ Configurazione OK")
                
                # Test aggiuntivi
                try:
                    from config import Config
                    Config.display_config()
                except Exception as e:
                    print(f"❌ Errore configurazione: {e}")
            return
    
    # Verifica setup
    if not check_setup():
        choice = input("\\nEseguire setup automatico? [Y/n]: ").strip().lower()
        if choice in ['', 'y', 'yes']:
            if not run_setup():
                print("❌ Setup fallito. Controlla errori sopra.")
                sys.exit(1)
        else:
            print("Setup richiesto per continuare.")
            print("Esegui: python start.py --setup")
            sys.exit(1)
    
    # Avvia bridge
    try:
        print("🚀 Avvio bridge...")
        from meshtastic_bridge import main
        main()
        
    except KeyboardInterrupt:
        print("\\n👋 Arresto richiesto dall'utente")
    except ImportError as e:
        print(f"❌ Errore import: {e}")
        print("Verifica che tutti i file siano presenti in src/")
    except Exception as e:
        print(f"❌ Errore: {e}")
        print("\\nPer debug dettagliato, modifica ENABLE_DEBUG=true in .env")

if __name__ == "__main__":
    main()