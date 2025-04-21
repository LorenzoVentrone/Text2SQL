import mariadb
import time
import os
from typing import List, Optional, Tuple
from fastapi import HTTPException


class DatabaseManager:
    def __init__(self) -> None:
        """
        Inizializza la connessione al database.
        Tenta di connettersi al database fino a 10 volte con un delay di 2 secondi tra i tentativi.
        I parametri di connessione sono letti da variabili di ambiente.
        """
        retries = 10
        delay = 2

        # Legge sempre da env; se non definito, usa i default per il locale
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = int(os.getenv("DB_PORT", 3307))
        db_user = os.getenv("DB_USER", "lorenzo")
        db_password = os.getenv("DB_PASSWORD", "pwd")
        db_name = os.getenv("DB_NAME", "movies_db")

        for attempt in range(1, retries+1):
            try:
                self.connection = mariadb.connect(
                    user=db_user,
                    password=db_password,
                    host=db_host,
                    port=db_port,
                    database=db_name
                )
                print(f"Connessione al DB riuscita ({db_host}:{db_port}).")
                break
            except mariadb.OperationalError as e:
                print(f"Tentativo {attempt}/{retries} fallito: {e}. Riprovo in {delay}s…")
                time.sleep(delay)
        else:
            raise RuntimeError(f"Impossibile connettersi al DB {db_host}:{db_port} dopo {retries} tentativi.")



    #Esecuzione della query
    def execute_query(self, query: str, params: tuple = None, return_columns: bool = True) -> Tuple[list[tuple], Optional[List[str]]]:
        """
        Esegue una query sul database e restituisce i risultati.

        :param query: La stringa della query SQL da eseguire.
        :param params: Una tupla contenente i parametri della query (opzionale).
        :param return_columns: Specifica se restituire anche i nomi delle colonne della tabella (opzionale, default: True).

        :return: Se `return_columns` è True, restituisce una tupla contenente:
                - result: Una lista di tuple con i risultati della query.
                - column_names: Una lista con i nomi delle colonne della tabella.
                Se `return_columns` è False, restituisce solo `result`.
        """
        cursor: mariadb.Cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description] if return_columns else None
        self.connection.commit()
        cursor.close()
        return (result, column_names) if return_columns else result

    #Esecuzione della query per operazioni nel database (INSERT, UPDATE, ...)
    def execute_db_operation(self, query: str, data: List[tuple]) -> None:
        """
        Esegue un'operazione di modifica sul database (ad esempio, INSERT, UPDATE o DELETE).

        :param query: La stringa della query SQL da eseguire.
        :param data: Una lista di tuple contenenti i valori da utilizzare nella query.
        """
        cursor: mariadb.Cursor = self.connection.cursor()
        try:
            if data:  # Esegui `executemany` solo se `data` non è vuoto
                cursor.executemany(query, data)
            else:  # Per query come DELETE senza parametri
                cursor.execute(query)
            self.connection.commit()
        except mariadb.Error as e:
            print(f"DEBUG: Errore durante l'esecuzione della query '{query}': {e}")
            raise
        finally:
            cursor.close()

    #Check per tabella del db vuota
    def table_is_empty(self, table: str) -> bool:
        """
        Verifica se una tabella del database è vuota.

        :param table: Il nome della tabella da controllare.

        :return: True se la tabella è vuota (non contiene righe), False altrimenti.
        """
        self.connection.commit()  # Forza la sincronizzazione della connessione
        result= self.execute_query(f"SELECT COUNT(*) FROM {table}",return_columns=False)

        return result[0][0] == 0

    #Estrazione dei dati dal file tsv
    def get_data(self) -> List[List[str]]:
            
        try:
            with open("data.tsv", "r") as file:
                db = []
                for line in file:
                    data = line.strip().split('\t')
                    db.append(data)
            return db
    
        except FileNotFoundError:
            raise ValueError("Il file 'data.tsv' non è stato trovato nella directory corrente.")
        except Exception as e:
            raise ValueError(f"Errore durante la lettura del file 'data.tsv': {e}")

    #Aggiunta dei registi nel db
    def add_directors(self, addRequest: List = None, data: List =  None) -> None:
        """
        Inserisce i dati nella tabella 'directors'.

        :param addRequest: [Opzionale]Per la richiesta di aggiunta successiva all'inizializzazione (default None)
        :param data: [Opzionale]Dati di inizializzazione del DB (Default None)
        """
        if self.table_is_empty("directors"):
            if data is not None:
                unique_directors = list(set((data[i][1], int(data[i][2])) for i in range(1, len(data))))
        elif addRequest is not None:
            # Controlla se il regista esiste già
            director_name = addRequest[1]
            existing_director = self.execute_query(
                "SELECT COUNT(*) FROM directors WHERE name = ?", (director_name,), return_columns=False
            )
            if existing_director[0][0] > 0:
                return
            unique_directors = [(addRequest[1], int(addRequest[2]))]
        else:
            raise ValueError("I dati per l'aggiunta non sono stati forniti.")
        self.execute_db_operation(
            "INSERT INTO directors (name, age) VALUES (?, ?)",
            unique_directors
        )

    #Aggiunta dei film nel db
    def add_movies(self, addRequest: List = None, data: List = None) -> None:
        """
        Inserisce i dati nella tabella 'movies'.

        :param addRequest: [Opzionale]Per la richiesta di aggiunta successiva all'inizializzazione (default None)
        :param data: [Opzionale]Dati di inizializzazione del DB (Default None)
        """
        if self.table_is_empty("movies"):
            if data is not None:
                movies_data = [
                    (data[i][0], data[i][1], int(data[i][3]), data[i][4])
                    for i in range(1, len(data))
                ]
        elif addRequest is not None:
            movies_data = [
                (addRequest[0], addRequest[1], int(addRequest[3]), addRequest[4])
            ]
        else:
            raise ValueError("I dati per l'aggiunta non sono stati forniti.")
        self.execute_db_operation(
            "INSERT INTO movies (title, director, year, genre) VALUES (?, ?, ?, ?)",
            movies_data
        )

    #Aggiunta di film/piattaforma nel db
    def add_platform_availability(self, addRequest: List = None, data: List = None) -> None:
        """
        Inserisce i dati nella tabella 'platform_availability'.

        :param addRequest: [Opzionale]Per la richiesta di aggiunta successiva all'inizializzazione (default None)
        :param data: [Opzionale]Dati di inizializzazione del DB (Default None)

        """
        if self.table_is_empty("platform_availability"):
            if data is not None:
                platform_data = []
                for i in range(1, len(data)):
                    movie_id = self.get_movie_id(data[i][0])

                    # Controlla se data[i][5] esiste ed è valido
                    if len(data[i]) > 5 and data[i][5]:
                        platform_data.append((movie_id, data[i][5]))

                    # Controlla se data[i][6] esiste ed è valido
                    if len(data[i]) > 6 and data[i][6]:
                        platform_data.append((movie_id, data[i][6]))

        elif addRequest is not None:
            movie_id = self.get_movie_id(addRequest[0])
            if len(addRequest) == 6:
                platform_data = [(movie_id, addRequest[5])]
            else:
                platform_data = [(movie_id, addRequest[5]), (movie_id, addRequest[6])]
        else:
            raise ValueError("I dati per l'aggiunta non sono stati forniti.")
        self.execute_db_operation(
            "INSERT INTO platform_availability (movie_id, platform) VALUES (?, ?)",
            platform_data
        )

    #Getter del movie_id dal db
    def get_movie_id(self, title: str) -> int:
        """
        Ottiene l'ID del film dato il titolo.

        :param title: Titolo del film
        :return: movie id
        """
        result = self.execute_query("SELECT id FROM movies WHERE title = ?", (title,),return_columns=False)
        return result[0][0]

    #Inizializzazione/update del database  
    def add_in_db(self, data_values: List[str], isFill: bool = True) -> None:
        try:
            if isFill:
                if len(data_values) < 5 or len(data_values)>7:
                    raise HTTPException(status_code=422, detail="Input non valido.")
                print("DEBUG: Aggiunta dati con isFill=True")
                self.add_directors(addRequest=data_values)
                self.add_movies(addRequest=data_values)
                self.add_platform_availability(addRequest=data_values)
            else:
                print("DEBUG: Aggiunta dati con isFill=False")
                self.add_directors(data=data_values)
                self.add_movies(data=data_values)
                self.add_platform_availability(data=data_values)
        except HTTPException as e:
            print(f"DEBUG: HTTPException catturata: {e.detail}")
            raise e
        except Exception as e:
            print(f"DEBUG: Errore interno: {e}")
            raise HTTPException(status_code=500, detail=f"Errore interno: {e}")
        

    #Chiusura della connessione
    def close_connection(self) -> None:
        """
        Chiude la connessione al database.
        """
        self.connection.close()

    #Ripulisce il database
    def clear_db(self) -> None:
        """
        Cancella i dati da tutte le tabelle del database.
        """
        try:
            # Elimina i dati dalle tabelle rispettando l'ordine delle dipendenze
            self.execute_db_operation("DELETE FROM platform_availability", [])
            self.execute_db_operation("DELETE FROM movies", [])
            self.execute_db_operation("DELETE FROM directors", [])
            print("DEBUG: Database ripulito con successo.")
        except mariadb.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        
