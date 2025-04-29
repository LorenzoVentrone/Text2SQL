from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List
from fastapi.middleware.cors import CORSMiddleware
import mariadb

from db_manager.DatabaseManager import DatabaseManager
from query_handler.QueryHandler import QueryHandler

# Inizializzazione FastAPI
app = FastAPI(title="Text2SQL-server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instanzia il DB manager
db_manager = DatabaseManager()

# Pulizia e riempimento del DB al lancio 
if not db_manager.is_init():
    try:
        print("DEBUG: Inizializzazione DB")
        db_manager.add_in_db(db_manager.get_data(), isFill=False)
    except Exception as e:
        raise RuntimeError(f"Errore inizializzazione database: {e}")

#Inizializzazione del gestore delle query
query_handler = QueryHandler()



# -- MODELLI PYDANTIC --
class TableSchema(BaseModel):
    table_name: str
    table_column: str

class Property(BaseModel):
    property_name: str
    property_value: str

class SearchResult(BaseModel):
    item_type: str
    properties: list[Property]

class DataInput(BaseModel):
    data_line: str
    
# -- ENDPOINTS --

#Metodo get per ottenere, seguendo il modello JSON richiesto, lo schema delle tabelle
@app.get("/schema_summary",response_model=list[TableSchema])
def schema_summary() -> List[Dict[str, Any]]:
    """
    Endpoint per eseguire la visualizzazione delle tabelle del DB.

    :return: I risultati della query formattati.
    """
    try:
        # execute_query per eseguire le query "SHOW TABLES"
        tables = db_manager.execute_query("SHOW TABLES",return_columns=False)

        schema = []

        for (table_name,) in tables:
            # execute_query per eseguire la query "SHOW COLUMS from table_name"
            columns = db_manager.execute_query(f"SHOW COLUMNS FROM {table_name}",return_columns=False)
            for column in columns:
                #Organizzazione nel formato JSON richiesto
                schema.append({"table_name": table_name, "table_column": column[0]})

        return schema

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    

#Metodo get per la search nel database data una question in linguaggio naturale 
@app.get("/search/{question}", response_model=List[SearchResult])
def search(question: str) -> List[Dict[str, Any]]:
    """
    Endpoint per eseguire una query basata su una domanda in linguaggio naturale.

    :param question: La domanda in linguaggio naturale.
    :return: I risultati della query formattati.
    """
    return query_handler.execute_query(question)
    

#Metodo post per aggiunta di dati al database   
@app.post("/add")
def add_data(input_data: DataInput) -> Dict[str, str]:
    """
    Endpoint per aggiungere una riga al database.

    :param input_data: Dati in formato JSON con il nome della tabella e la riga da inserire.
    :return: Stato dell'operazione.
    """
    try:
        # Processa la stringa data_line e dividila in una lista di valori
        data_values = input_data.data_line.split(',')

        # Aggiungi i dati al database utilizzando la funzione add_in_db
        db_manager.add_in_db(data_values)

        # Restituisci lo stato dell'operazione
        return {"status": "ok"}
    except ValueError as e:
        # Errore di validazione (es. numero di colonne errato o violazione di chiave primaria)
        raise HTTPException(status_code=422, detail=str(e))







