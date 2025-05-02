import os
from fastapi import FastAPI, Query, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from urllib.parse import quote
import requests


# Configurazione del frontend
app = FastAPI(title="Text2SQL-client")

# Configurazione Jinja2 in base all'ambiente
if os.getenv("DOCKER_ENV", False):
    templates = Jinja2Templates(directory="/app/templates")
else:
    templates = Jinja2Templates(directory="templates")


# URL del backend (configurabile via env)
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """
    Visualizza la homepage con il form e i risultati, se presenti.

    :param request: Oggetto Request di FastAPI che rappresenta la richiesta HTTP.
    :return: La pagina HTML della homepage.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, question: str = Query(...)) -> HTMLResponse:
    """
    Invia una domanda al backend come GET per la ricerca nel DB e mostra i risultati.

    :param request: Oggetto Request di FastAPI che rappresenta la richiesta HTTP.
    :param question: La domanda da inviare al backend per la ricerca.

    :return: La pagina HTML con i risultati della ricerca o un messaggio di errore.
    """
    try:
        # encoded_question per lettura del "?" nella question
        encoded_question = quote(question)
        response = requests.get(f"{BASE_URL}/search/{encoded_question}")
        response.raise_for_status()
        results = response.json()
        return templates.TemplateResponse("index.html", {"request": request, "results": results, "question": question})
    except requests.exceptions.HTTPError as e:
        # Gestione specifica per errore 422
        if e.response.status_code == 422:
            error_message = "La domanda inserita non è valida. Per favore, verifica e riprova."
        else:
            error_message = e.response.json().get("detail", "Errore durante la richiesta.")
        return templates.TemplateResponse("index.html", {"request": request, "error": error_message})
    except requests.exceptions.RequestException as e:
        # Gestione generica per errori di connessione o altro
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})


@app.post("/add", response_class=HTMLResponse)
def add_data(request: Request, data_line: str = Form(...)) -> HTMLResponse:
    """
    Invia una nuova riga da aggiungere al backend.

    :param request: Oggetto Request di FastAPI che rappresenta la richiesta HTTP.
    :param data_line: Dati da aggiungere al backend.

    :return: La pagina HTML con un messaggio di successo o di errore.
    """
    try:
        response = requests.post(f"{BASE_URL}/add", json={"data_line": data_line})
        response.raise_for_status()
        return templates.TemplateResponse("index.html", {"request": request, "success": "Dati aggiunti con successo!"})
    except requests.exceptions.HTTPError as e:
        # Gestione specifica per errori HTTP
        error_message = e.response.json().get("detail", "Errore durante l'aggiunta dei dati.")
        return templates.TemplateResponse("index.html", {"request": request, "error": error_message})
    except requests.exceptions.RequestException as e:
        # Gestione generica per errori di connessione o altro
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})


@app.get("/schema", response_class=HTMLResponse)
def show_schema(request: Request) -> HTMLResponse:
    """
    Recupera lo schema del database (tabelle e colonne).

    :param request: Oggetto Request di FastAPI che rappresenta la richiesta HTTP.

    :return: La pagina HTML con un messaggio di successo o di errore.
    """
    try:
        response = requests.get(f"{BASE_URL}/schema_summary")
        response.raise_for_status()
        schema = response.json()
        return templates.TemplateResponse("index.html", {"request": request, "schema": schema})
    except requests.exceptions.RequestException as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})
    
    
@app.get("/about", response_class=HTMLResponse)
def about(request: Request) -> HTMLResponse:
    """
    Visualizza la pagina About con informazioni sull'applicazione.

    :param request: Oggetto Request di FastAPI che rappresenta la richiesta HTTP.
    :return: La pagina HTML con le informazioni sull'applicazione.
    """
    return templates.TemplateResponse("about.html", {"request": request})

