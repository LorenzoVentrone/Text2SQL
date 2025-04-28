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
        except mariadb.IntegrityError as e:
            # Gestione specifica per violazione di chiave primaria
            if "Duplicate entry" in str(e):
                print(f"DEBUG: Violazione della chiave primaria: {e}")
                raise HTTPException(status_code=409, detail="Violazione della chiave primaria: il record esiste già.")
            else:
                print(f"DEBUG: Errore di integrità del database: {e}")
                raise HTTPException(status_code=422, detail=f"Errore di integrità del database: {e}")
        except mariadb.Error as e:
            print(f"DEBUG: Errore durante l'esecuzione della query '{query}': {e}")
            raise HTTPException(status_code=500, detail=f"Errore interno del database: {e}")
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
        """
        Estrae i dati dal file .tsv, ripulisce da tutti i caratteri in eccesso e li inserisce in una lista.

        :return: Restituisce una Lista contente Liste di stringhe con tutti i campi estratti dal file
        """
            
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
        

    def add_directors(self, addRequest: List = None, data: List = None) -> bool:
        """
        Inserisce o aggiorna i dati nella tabella 'directors'.

        :param addRequest: [Opzionale] Per la richiesta di aggiunta successiva all'inizializzazione (default None)
        :param data: [Opzionale] Dati di inizializzazione del DB (Default None)

        :return: True se è stato aggiunto o aggiornato almeno un elemento, False altrimenti
        """
        unique_directors = []
        if self.table_is_empty("directors"):
            if data is not None:
                unique_directors = list(set((data[i][1], int(data[i][2])) for i in range(1, len(data))))
        elif addRequest is not None:
            director_name = addRequest[1]
            director_age = int(addRequest[2])

            # Verifica se il regista esiste già
            existing_director = self.execute_query(
                "SELECT age FROM directors WHERE name = ?", (director_name,), return_columns=False
            )

            if existing_director:
                current_age = existing_director[0][0]
                # Aggiorna il regista se l'età è diversa
                if current_age != director_age:
                    self.execute_db_operation(
                        "UPDATE directors SET age = ? WHERE name = ?", [(director_age, director_name)]
                    )
                    print(f"DEBUG: Aggiornato il regista '{director_name}' con la nuova età {director_age}.")
                    return True # Non aggiungere un nuovo record se è stato aggiornato
            else:
                # Se il regista non esiste, aggiungilo
                unique_directors = [(director_name, director_age)]
        else:
            raise ValueError("I dati per l'aggiunta non sono stati forniti.")

        if unique_directors:
            self.execute_db_operation(
                "INSERT INTO directors (name, age) VALUES (?, ?)",
                unique_directors
            )
            print(f"DEBUG: Aggiunto il regista '{unique_directors[0][0]}'.")
            return True  # Aggiunto

        print("DEBUG: Nessun regista aggiunto.")
        return False  # Nessun elemento aggiunto

    #Aggiunta dei film nel db
    def add_movies(self, addRequest: List = None, data: List = None) -> bool:
        """
        Inserisce i dati nella tabella 'movies' solo se non esistono duplicati.

        :param addRequest: [Opzionale] Per la richiesta di aggiunta successiva all'inizializzazione (default None)
        :param data: [Opzionale] Dati di inizializzazione del DB (Default None)

        :return: True se è stato aggiornato almeno un elemento, False altrimenti
        """

        if self.table_is_empty("movies"):
            if data is not None:
                movies_data = [
                    (data[i][0], data[i][1], int(data[i][3]), data[i][4])
                    for i in range(1, len(data))
                ]
        elif addRequest is not None:
            # Verifica se il film esiste già
            movie_title = addRequest[0]
            director_name = addRequest[1]
            movie_year = int(addRequest[3])
            movie_genre = addRequest[4]
            existing_movie = self.execute_query(
                "SELECT director, year, genre FROM movies WHERE title = ?", (movie_title,), return_columns=False
            )

            if existing_movie:
                current_director, current_year, current_genre = existing_movie[0]
                # Controlla se i campi sono uguali
                updates = []
                if current_director != director_name:
                    updates.append(f"director = '{director_name}'")
                if current_year != movie_year:
                    updates.append(f"year = {movie_year}")
                if current_genre != movie_genre:
                    updates.append(f"genre = '{movie_genre}'")

                if updates:
                    update_query = f"UPDATE movies SET {', '.join(updates)} WHERE title = ?"
                    self.execute_db_operation(update_query, [(movie_title,)])
                    print(f"DEBUG: Aggiornato il film '{movie_title}' con i nuovi valori: {updates}.")
                    return True#aggiornato i campi -> esce
                else:
                    print(f"DEBUG: Il film '{movie_title}' esiste già con gli stessi valori. Nessuna aggiunta.")
                    return  False# Non aggiungere nulla se i campi sono uguali

            # Aggiungi il film solo se i campi sono diversi
            movies_data = [
                (movie_title, director_name, movie_year, movie_genre)
            ]
        else:
            raise ValueError("I dati per l'aggiunta non sono stati forniti.")

        if movies_data:
            self.execute_db_operation(
                "INSERT INTO movies (title, director, year, genre) VALUES (?, ?, ?, ?)",
                movies_data
            )
            print(f"DEBUG: Aggiunto il film '{movies_data[0][0]}'.")
            return True  # Aggiunto

        print("DEBUG: Nessun film aggiunto.")
        return False  # Nessun elemento aggiunto

    #Aggiunta/Aggiornamento di film/piattaforma nel db
    def add_platform_availability(self, addRequest: List = None, data: List = None) -> bool:
        """
        Inserisce i dati nella tabella 'platform_availability' solo se non esistono duplicati.

        :param addRequest: [Opzionale] Per la richiesta di aggiunta successiva all'inizializzazione (default None)
        :param data: [Opzionale] Dati di inizializzazione del DB (Default None)

        :return: True se è stato aggiornato almeno un elemento, False altrimenti
        """
        platform_data = []

        if self.table_is_empty("platform_availability"):
            # Inizializzazione con dati
            if data is not None:
                for i in range(1, len(data)):
                    movie_id = self.get_movie_id(data[i][0])

                    # Controlla se data[i][5] esiste ed è valido
                    if len(data[i]) > 5 and data[i][5]:
                        platform_data.append((movie_id, data[i][5]))

                    # Controlla se data[i][6] esiste ed è valido
                    if len(data[i]) > 6 and data[i][6]:
                        platform_data.append((movie_id, data[i][6]))

        elif addRequest:
            movie_id = self.get_movie_id(addRequest[0])

            # Estrai le piattaforme dall'input
            platform1 = addRequest[5] if len(addRequest) > 5 and addRequest[5].strip() else None
            platform2 = addRequest[6] if len(addRequest) > 6 and addRequest[6].strip() else None

            # Elimina i record esistenti se entrambe le piattaforme sono `None`
            if not platform1 and not platform2:
                self.execute_db_operation(
                    "DELETE FROM platform_availability WHERE movie_id = ?", [(movie_id,)]
                )
                print(f"DEBUG: Eliminati i record esistenti per movie_id {movie_id}.")
                return True #Aggiornato: eliminazione dati dal DB

            # Aggiungi piattaforme valide
            if platform1:
                platform_data.append((movie_id, platform1))
            if platform2:
                platform_data.append((movie_id, platform2))

        # Inserisci i nuovi dati se presenti
        if platform_data:
            # Elimina i record esistenti per il `movie_id`
            self.execute_db_operation(
                "DELETE FROM platform_availability WHERE movie_id = ?", [(movie_id,)]
            )
            # Inserisci i nuovi record
            self.execute_db_operation(
                "INSERT INTO platform_availability (movie_id, platform) VALUES (?, ?)",
                platform_data
            )
            print(f"DEBUG: Aggiunti/Aggiornati {len(platform_data)} record in 'platform_availability'.")
            return True

        print("DEBUG: Nessun dato aggiunto a 'platform_availability'.")
        return False
    

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
        """
        Inserimento o inizializzazione del database

        :param data_values: Lista di stringhe da inserire nel database
        :param isFill: [Opzionale] Modalità di inserimento: aggiunta/update[Default True] oppure inizializzazione[False]

        """
        try:
            #Se il DB è già stato inizializzato
            if isFill: 
                if len(data_values) < 5 or len(data_values)>7:
                    raise HTTPException(status_code=422, detail="Input non valido (La lunghezza dell'input deve essere < 5 o > 7).")
                added_directors = self.add_directors(addRequest=data_values)
                added_movies = self.add_movies(addRequest=data_values)
                added_platform = self.add_platform_availability(addRequest=data_values)
            # Inizializzazione del DB
            else:
                print("DEBUG: Aggiunta dati con isFill=False")
                added_directors = self.add_directors(data=data_values)
                added_movies = self.add_movies(data=data_values)
                added_platform = self.add_platform_availability(data=data_values)

            #Se non è stato aggiunto nessun elemento 
            if not (added_directors or added_movies or added_platform):
                print("DEBUG: nessun elemento aggiunto condizione")
                raise HTTPException(status_code=409, detail="Campo già presente, nessun elemento aggiunto")

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