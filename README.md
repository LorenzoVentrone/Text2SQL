# Text2SQL 💬

**Text2SQL** è un'applicazione web che consente di convertire domande in linguaggio naturale in query SQL eseguibili su un database relazionale. Il progetto è composto da un backend sviluppato con FastAPI e un frontend interattivo, offrendo un'interfaccia user-friendly per interrogare e gestire i dati.

## 🚀 Funzionalità principali

- **Interrogazione in linguaggio naturale**: Inserisci domande come "Elenca i film del 2020" e ottieni i risultati direttamente dal database.
- **Visualizzazione dello schema**: Esplora le tabelle e le colonne del database in modo strutturato.
- **Aggiunta di dati**: Inserisci nuove righe nel database attraverso il frontend.
- **Interfaccia intuitiva**: Design moderno e responsivo per una migliore esperienza utente.


## 🐳 Avvio rapido con Docker

Assicurati di avere Docker e Docker Compose installati sul tuo sistema. Per avviare l'applicazione:

```bash
git clone https://github.com/LorenzoVentrone/Text2SQL.git
cd Text2SQL
docker-compose up --build
```
L'applicazione sarà disponibile all'indirizzo ```localhost:8001```

## ⚙️ Configurazione manuale (senza Docker)
### Backend
- Naviga nella directory backend: ```cd backend/src```

- Installa le dipendenze: ```pip install -r requirements.txt```

- Avvia il server FastAPI: ```uvicorn backend.backend:app --reload```
  - Se necessario esportare il PYTHONPATH eseguendo ```PYTHONPATH=$(pwd)/src uvicorn backend.backend:app --reload```

### Frontend
- Assicurati che il backend sia in esecuzione.
- Naviga nella directory src: ```cd frontend/src```
- Installa le dipendenze: ```pip install -r requirements.txt```
- Avvia il server FastAPI: ```uvicorn frontend.frontend:app --reload --port 8001```
  - Se necessario esportare il PYTHONPATH eseguendo ```PYTHONPATH=$(pwd)/src uvicorn frontend.frontend:app --reload --port 8001```

### MariaDB

- Il progetto include una configurazione Docker per avviare un container MariaDB e inizializzare automaticamente il database all'avvio.
  
- All'interno della cartella `mariadb_init/` è presente uno script SQL (`init.sql`) che viene eseguito automaticamente dal container MariaDB al primo avvio. Questo script definisce le tabelle e    inserisce eventuali dati di partenza.

- Avvio del container MariaDB

  - Assicurati di essere nella root del progetto, quindi esegui:```docker-compose up -d mariadb```
### Esecuzione
L'applicazione sarà disponibile all'indirizzo ```localhost:8001```

## 🔍 Query supportate

L'applicazione attualmente supporta le seguenti domande in linguaggio naturale:

- **"Elenca i film del \<Anno\>."**  
  → Restituisce i film usciti nell’anno indicato.

- **"Quali sono i registi presenti su \<Piattaforma\>?"**  
  → Elenca i registi con film disponibili sulla piattaforma specificata.

- **"Elenca tutti i film di \<Genere\>."**  
  → Mostra tutti i film del genere specificato.

- **"Quali film sono stati fatti da un regista di almeno \<Età\> anni?"**  
  → Mostra i film diretti da registi con età maggiore o uguale a quella indicata.

- **"Quali registi hanno fatto più di un film?"**  
  → Restituisce i registi con almeno due film nel database.

## ✍️ Formattazione per l'inserimento dati

Per aggiungere una nuova riga nel database, è necessario seguire questo formato (valori separati da virgole):
`Titolo,NomeRegista,EtàRegista,Anno,Genere,Piattaforma1[,Piattaforma2] `

- I primi 5 campi sono **obbligatori**.
- `Piattaforma1` e `Piattaforma2`sono **facoltativi**

### Esempio:
`Inception,Christopher Nolan,50,2010,Sci-Fi,Netflix,PrimeVideo`

## 🛠️ Tecnologie utilizzate

Backend: FastAPI, MariaDB

Frontend: HTML, CSS (con Jinja2 per il templating)

Containerizzazione: Docker, Docker Compose




