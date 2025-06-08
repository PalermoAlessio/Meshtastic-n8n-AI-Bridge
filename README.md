# 📡 Meshtastic ↔ n8n AI Bridge

Sistema intelligente che trasforma la tua rete **Meshtastic LoRa** in una rete di comunicazione automatizzata con **intelligenza artificiale**. Permette di creare bot AI che rispondono automaticamente ai messaggi ricevuti via radio, rendendo i nodi Meshtastic veri e propri assistenti virtuali distribuiti.

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)

## 🎯 Caratteristiche

- **📥 Ricezione automatica** di messaggi Meshtastic via seriale
- **🔄 Bridge bidirezionale** tra Meshtastic e n8n
- **🤖 Bot automatico** con logiche personalizzabili in n8n
- **⚡ Threading asincrono** per prestazioni ottimali
- **🔒 Gestione coda** per evitare conflitti porta seriale
- **📊 Logging dettagliato** per debugging

## 🏗️ Architettura

```
📡 Dispositivo Meshtastic (LoRa)
           ↕️ USB/Seriale
    🐍 Python Bridge Server
           ↕️ HTTP/Webhook
      🌐 n8n (Automazione)
```

## 🚀 Quick Start

### Prerequisiti

- Python 3.7+
- Dispositivo Meshtastic configurato
- n8n installato e configurato
- Porta seriale disponibile (es. COM3, /dev/ttyUSB0)

### Installazione

1. **Clona il repository:**
```bash
git clone https://github.com/PalermoAlessio/meshtastic-n8n-bridge.git
cd meshtastic-n8n-bridge
```

2. **Installa le dipendenze:**
```bash
pip install -r requirements.txt
```

3. **Installa Meshtastic CLI:**
```bash
pip install meshtastic
```

### Configurazione Rapida

1. **Configura n8n:**
   - Importa il workflow da `workflows/meshtastic-bot.json`
   - Attiva il workflow

2. **Avvia il bridge:**
```bash
python src/meshtastic_bridge.py
```

3. **Inserisci le impostazioni:**
   - Porta seriale (es. `COM3`)
   - URL webhook n8n (default: `http://localhost:5678/webhook/meshtastic`)

## 📖 Configurazione Dettagliata

### 1. Setup Dispositivo Meshtastic

Assicurati che il tuo dispositivo Meshtastic sia:
- Connesso via USB alla porta corretta
- Configurato con il canale desiderato
- In grado di decrittografare messaggi del canale

### 2. Setup n8n

Importa il workflow fornito in `workflows/meshtastic-bot.json` che include:

- **Webhook Trigger**: Riceve messaggi da Meshtastic
- **Function Node**: Logica di risposta personalizzabile
- **HTTP Request**: Invia risposte al bridge

### 3. Configurazione Bridge

Il bridge può essere configurato modificando le variabili in `config.py`:

```python
# Configurazione di default
WEBHOOK_URL = "http://localhost:5678/webhook/meshtastic"
HTTP_PORT = 8888
SERIAL_BAUDRATE = 115200
QUEUE_PROCESS_INTERVAL = 2  # secondi
```

## 🔧 Uso Avanzato

### Personalizzazione Logica Bot

Modifica il nodo AI Agent in n8n per creare risposte personalizzate. Il sistema utilizza intelligenza artificiale per generare risposte automatiche ai messaggi Meshtastic, mantenendo una memoria della conversazione per chat più naturali.

Il bot risponde automaticamente a qualsiasi messaggio ricevuto tramite la rete LoRa, rendendo il tuo nodo Meshtastic un vero assistente AI distribuito.

### Logging e Monitoraggio

Il sistema fornisce logging dettagliato:

```
💬 [23:08:21] Da: 0x433df694
📝 Messaggio: Ciao bot!
✅ Inviato a n8n: Ciao bot!
📤 Aggiunto alla coda...
✅ Inviato: Ciao anche a te! → !433df694
```

### API HTTP

Il bridge espone un'API HTTP su `http://localhost:8888`:

- **POST /**: Invia messaggio Meshtastic
- **GET /**: Status check

Esempio richiesta:
```json
{
    "to": "0x433df694",
    "message": "Risposta automatica"
}
```

## 🛠️ Sviluppo

### Struttura Progetto

```
meshtastic-n8n-bridge/
├── src/
│   ├── meshtastic_bridge.py      # Bridge principale
│   ├── message_handler.py        # Gestione messaggi
│   ├── serial_manager.py         # Gestione porta seriale
│   └── config.py                 # Configurazione
├── workflows/
│   └── meshtastic-bot.json       # Workflow n8n
├── docs/
│   ├── setup-guide.md            # Guida setup dettagliata
│   ├── api-reference.md          # Documentazione API
│   └── troubleshooting.md        # Risoluzione problemi
├── examples/
│   ├── basic-bot.py              # Bot esempio base
│   └── advanced-responses.js     # Risposte avanzate n8n
├── tests/
│   └── test_bridge.py            # Test automatici
├── requirements.txt              # Dipendenze Python
├── README.md                     # Questo file
└── LICENSE                       # Licenza MIT
```

### Contribuire

1. Fork del repository
2. Crea branch feature (`git checkout -b feature/nuova-funzione`)
3. Commit modifiche (`git commit -am 'Aggiunge nuova funzione'`)
4. Push al branch (`git push origin feature/nuova-funzione`)
5. Crea Pull Request

## 🐛 Troubleshooting

### Problemi Comuni

**❌ Errore porta seriale in uso:**
```
Soluzione: Chiudi altri programmi che usano la porta (Arduino IDE, ecc.)
```

**❌ Messaggi non ricevuti:**
```
Verifica: Configurazione canale Meshtastic, decrittografia abilitata
```

**❌ n8n non risponde:**
```
Controlla: URL webhook, workflow attivo, connessione di rete
```


## 📊 Esempi d'Uso

### 🤖 Assistente AI Distribuito
Ogni nodo Meshtastic diventa un assistente intelligente che può rispondere a domande, fornire informazioni e mantenere conversazioni naturali.

### 🌐 Rete di Comunicazione Intelligente
Crea una rete mesh dove i nodi possono comunicare automaticamente e intelligentemente tra loro.

### 📡 Bot di Servizio
Configura bot specializzati per servizi specifici: meteo, notizie, calcoli, o qualsiasi altro servizio automatizzato.

### 🏔️ Comunicazioni Remote
Ideale per escursionisti, operatori di emergenza, o team di lavoro in aree senza copertura cellulare che necessitano di assistenti automatici.


## 📄 Licenza

Questo progetto è rilasciato sotto [MIT License](LICENSE).

## 🙏 Riconoscimenti

- [Meshtastic Project](https://meshtastic.org/) per l'incredibile piattaforma LoRa
- [n8n.io](https://n8n.io/) per lo strumento di automazione
- Community open source per supporto e contributi

---

⭐ **Se questo progetto ti è utile, lascia una stella!** ⭐

Realizzato con ❤️ da [Alessio Palermo](https://github.com/PalermoAlessio) per la community Meshtastic
