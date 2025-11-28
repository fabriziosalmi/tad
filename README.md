# TAZCOM: Tactical Autonomous Zone Communications

**[ Stato Progetto: FASE 1 - COMPLETE ✅ | MVP Production-Ready ]**

*"La rete non è qualcosa che usi. La rete è dove sei. La rete siamo noi."*

---

## 🎉 FASE 1 COMPLETE - MVP READY!

**TAZCOM** è ora un sistema di comunicazione P2P **funzionante e pronto per l'uso**, con:
- ✅ **Discovery automatico** dei peer su rete locale
- ✅ **Chat multi-canale** con interfaccia terminale avanzata
- ✅ **Canali privati** con crittografia end-to-end (AES-256-GCM)
- ✅ **Persistenza messaggi** con database SQLite
- ✅ **Identità crittografiche** con firma digitale Ed25519
- ✅ **96% test coverage** (93/97 test passing)

**👉 [Vai alla Quick Start Guide](START_HERE.md) per iniziare subito!**

---

## Quick Start (30 secondi)

```bash
# 1. Installa dipendenze
pip install -r requirements.txt

# 2. Avvia il nodo
python -m tad.main

# 3. Usa i comandi della TUI:
/help                           # Lista comandi
/create #myChannel private      # Crea canale privato
/invite <node_id> #myChannel    # Invita qualcuno
```

I nodi si scoprono automaticamente - nessuna configurazione richiesta!

---

TAZCOM è un sistema di comunicazione tattico, decentralizzato e offline-first, progettato per prosperare negli ambienti in cui le infrastrutture tradizionali falliscono o sono assenti: i free party, i TAZ (Temporary Autonomous Zones), le manifestazioni e qualsiasi situazione in cui la community ha bisogno di autorganizzarsi in modo resiliente e sicuro.

Non è un'altra app di messaggistica. È uno strumento di sopravvivenza e coordinamento per la tribe.

### Indice

1.  [Il Manifesto: I Principi Fondamentali](#il-manifesto-i-principi-fondamentali)
2.  [Architettura Funzionale](#architettura-funzionale)
3.  [Feature Principali: Il Kit Tattico](#feature-principali-il-kit-tattico)
4.  [Visione Futura: Feature Secondarie](#visione-futura-feature-secondarie)
5.  [Roadmap di Sviluppo](#roadmap-di-sviluppo)
6.  [Stack Tecnologico Iniziale](#stack-tecnologico-iniziale)
7.  [Come Contribuire](#come-contribuire)
8.  [Licenza](#licenza)

---

### Il Manifesto: I Principi Fondamentali

TAZCOM è costruito su un'etica radicale di autonomia e resilienza. Ogni scelta di design deriva da questi principi:

*   **Offline First, Always.** Il sistema deve essere 100% funzionale senza accesso a internet o alla rete cellulare. La rete è formata dai dispositivi stessi, sul posto.
*   **Zero Configuration (Zero Sbatti).** L'utente avvia l'app e la connessione alla rete locale è automatica. Nessun IP, nessuna password, nessun account. Funziona e basta.
*   **Anonimato Reale.** L'identità è una chiave crittografica generata sul dispositivo, non collegata a email, numero di telefono o dati personali.
*   **Efemero di Natura (Leave No Trace).** Le comunicazioni sono progettate per svanire. I messaggi hanno un tempo di vita (TTL) e non vengono archiviati in modo permanente. La cronologia è una vulnerabilità.
*   **Sicurezza End-to-End.** Tutte le comunicazioni sono crittografate. Nessuno al di fuori del mittente e del destinatario (o del canale) può leggere i messaggi.
*   **Basso Consumo Energetico.** Ottimizzato per sopravvivere a eventi di più giorni su batterie di telefoni, power bank e generatori.

### Architettura Funzionale

TAZCOM non ha server. Ogni utente che esegue l'app diventa un **Nodo** della rete.

1.  **Il Nodo (Node):** Ogni dispositivo è un peer autonomo che detiene la propria identità crittografica.
2.  **La Rete Mesh (The Mesh):** I nodi si scoprono e si connettono direttamente tra loro utilizzando tecnologie a corto raggio come **Bluetooth Low Energy (BLE)** e **Wi-Fi Direct**. Creano una rete a maglie (mesh network) spontanea e auto-riparante.
3.  **La Propagazione (Gossip Protocol):** L'informazione si diffonde attraverso la rete come un pettegolezzo. Un nodo invia un messaggio ai suoi vicini, che a loro volta lo inoltrano ai loro, garantendo che l'informazione raggiunga tutta l'area dell'evento anche se non tutti i nodi sono direttamente connessi.

### Feature Principali: Il Kit Tattico

Queste sono le funzionalità fondamentali che TAZCOM fornirà nella sua prima versione stabile.

#### 1. TribeNet (Mesh Chat)
La spina dorsale della comunicazione.
*   **Canali Pubblici:** Canali tematici aperti a tutti i nodi della rete (es: `#mainfloor`, `#infopoint`, `#lostandfound`).
*   **Messaggi Privati:** Comunicazioni dirette e crittografate tra due nodi specifici.
*   **Propagazione Intelligente:** Il protocollo gossip assicura che i messaggi raggiungano la loro destinazione in modo efficiente.

#### 2. L'Eco (SAMU Relay)
Un sistema di allerta prioritario per la sicurezza e il supporto della community.
*   **Allerte Prioritarie:** Le richieste di aiuto (medico, acqua, supporto tecnico/legale) hanno la precedenza su tutti gli altri messaggi.
*   **Gestione dello Stato:** Le allerte hanno uno stato (`APERTO`, `PRESO IN CARICO`, `RISOLTO`) per un coordinamento efficace ed evitare duplicazioni di sforzi.
*   **Interfaccia Dedicata:** Una schermata chiara e semplice per visualizzare e gestire le allerte attive.

#### 3. Whisper (Dead Drops Digitali)
Per scambiare informazioni sensibili in modo sicuro e contestuale.
*   **Ancoraggio di Prossimità:** Lascia un messaggio crittografato "ancorato" a una zona, leggibile solo da chi si trova fisicamente nelle immediate vicinanze.
*   **Nessun GPS Coinvolto:** La prossimità è verificata tramite handshakes diretti a bassissima potenza (BLE/NFC), non tramite coordinate geografiche.
*   **Contenuto a Scadenza:** I "drop" sono temporanei e si autodistruggono dopo un tempo predefinito.

#### 4. VibeMap (Sonar di Densità)
Uno strumento di orientamento che rispetta l'anonimato della posizione.
*   **Radar di Densità:** Visualizza la "densità" di nodi TAZCOM nell'area circostante, senza mai mostrare posizioni precise su una mappa.
*   **Orientamento Relativo:** Usa la bussola del telefono per mostrare la direzione in cui la "vibrazione" della festa è più forte.
*   **Zero Dati di Posizione:** Non vengono mai scambiati dati GPS, rendendo l'informazione utile per i partecipanti ma strategicamente inutile per osservatori esterni.

### Visione Futura: Feature Secondarie

Una volta che il kit tattico sarà solido, TAZCOM potrà evolvere con nuovi moduli:

*   **Guerrilla Radio:** Streaming audio P2P a bassissima latenza per trasmettere un DJ set dal proprio telefono ai dispositivi vicini.
*   **File Drop:** Condivisione sicura di piccoli file (tracce audio, flyer, testi) tra nodi vicini.
*   **Sistema di Plugin:** Un'architettura che permetta alla community di sviluppare e integrare nuovi strumenti tattici.

### Roadmap di Sviluppo

Lo sviluppo seguirà un approccio iterativo e pragmatico.

*   **FASE 0: Protocollo & PoC (The Blueprint)**
    *   [ ] Definizione dettagliata delle specifiche del protocollo di comunicazione.
    *   [ ] Scelta dello stack tecnologico definitivo per il prototipo.
    *   [ ] Creazione di un Proof of Concept (PoC) che dimostri la discovery e la connessione tra 2 nodi.
*   **FASE 1: MVP - TribeNet (First Contact)**
    *   [ ] Implementazione del protocollo gossip e della chat su un canale pubblico.
    *   [ ] Creazione di un'interfaccia a riga di comando (CLI/TUI) per i test.
*   **FASE 2: SAMU Relay (The Guardian)**
    *   [ ] Implementazione della logica di priorità e gestione degli stati per le allerte.
*   **FASE 3: UI & Packaging (The Shell)**
    *   [ ] Sviluppo di un'interfaccia utente cross-platform semplice e intuitiva (es. Kivy, Flutter, PWA).
    *   [ ] Packaging dell'applicazione per una facile installazione (APK, etc.).
*   **FASE 4: Alpha sul Campo (Battesimo del Fuoco)**
    *   [ ] Testare l'applicazione con un gruppo ristretto di utenti fidati durante un vero evento.

### Stack Tecnologico Iniziale

Questo è lo stack proposto per la fase di prototipazione, scelto per la velocità di sviluppo e la flessibilità.

*   **Linguaggio:** Python 3
*   **Interfaccia Prototipo:** Textual (Terminal User Interface framework)
*   **Networking (Candidati):** `bleak` (BLE), `python-wifi` (Wi-Fi Direct), `py-multicast-dns` (mDNS)
*   **Crittografia:** `pynacl` (basato su libsodium)

### Come Contribuire

Questo progetto è aperto a chiunque condivida i suoi principi. Per ora, il focus è sulla definizione del protocollo. Vedi il file `PROJECT_STATUS.md` per i dettagli su cosa stiamo lavorando e dove serve aiuto.

### Licenza

Questo progetto è rilasciato sotto la licenza **MIT**. Sei libero di usare, modificare, distribuire e distruggere questo codice come meglio credi.

