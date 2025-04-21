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
def index(request: Request):
    """
    Visualizza la homepage con il form e i risultati, se presenti.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, question: str = Query(...)) -> HTMLResponse:
    """
    Invia una domanda al backend come GET e mostra i risultati.
    """
    try:
        # encoded_question per lettura del "?" nella question
        encoded_question = quote(question)
        response = requests.get(f"{BASE_URL}/search/{encoded_question}")
        response.raise_for_status()
        results = response.json()
        return templates.TemplateResponse("index.html", {"request": request, "results": results, "question": question})
    except requests.exceptions.RequestException as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})


@app.post("/add", response_class=HTMLResponse)
def add_data(request: Request, data_line: str = Form(...)) -> HTMLResponse:
    """
    Invia una nuova riga da aggiungere al backend.
    """
    try:
        response = requests.post(f"{BASE_URL}/add", json={"data_line": data_line})
        response.raise_for_status()
        return templates.TemplateResponse("index.html", {"request": request, "success": "Dati aggiunti con successo!"})
    except requests.exceptions.RequestException as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})


@app.get("/schema", response_class=HTMLResponse)
def show_schema(request: Request) -> HTMLResponse:
    """
    Recupera lo schema del database (tabelle e colonne).
    """
    try:
        response = requests.get(f"{BASE_URL}/schema_summary")
        response.raise_for_status()
        schema = response.json()
        return templates.TemplateResponse("index.html", {"request": request, "schema": schema})
    except requests.exceptions.RequestException as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})
    

