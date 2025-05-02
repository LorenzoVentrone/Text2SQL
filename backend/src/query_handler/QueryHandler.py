import re
from typing import Any, Dict, List, Tuple
from fastapi import HTTPException
from db_manager.DatabaseManager import DatabaseManager


class QueryHandler:
    def __init__(self):
        """
        Gestisce la mappatura di query in linguaggio naturale a query SQL e ne formatta i risultati.
        """
        self.db_manager = DatabaseManager()
        # Mapping tra pattern regex, tipo di item e query SQL
        self.query_mapping = {
            r"Elenca i film del (\d{4})": ("film","SELECT title as name,year,genre FROM movies WHERE year = ?"),
            r"Quali sono i registi presenti su (.+)\?": ("director", """
                SELECT DISTINCT d.name, d.age
                FROM directors d
                JOIN movies m ON d.name = m.director
                JOIN platform_availability p ON m.id = p.movie_id
                WHERE platform = ?
            """),
            r"Elenca tutti i film di (.+).": ("film","SELECT title as name,year,genre FROM movies WHERE genre = ?"),
            r"Quali film sono stati fatti da un regista di almeno (\d+) anni\?": ("film","""
                SELECT m.title as name,m.director,year
                FROM movies m 
                JOIN directors d ON m.director = d.name 
                WHERE d.age >= ?
            """),
            r"Quali registi hanno fatto più di un film\?":("director","""
                SELECT director as name, age, COUNT(*) "Numero film"
                FROM movies join directors d on name=director
                GROUP BY director 
                HAVING COUNT(*) > 1
            """)
}

    def match_query(self, question: str) -> Tuple[str, str, Tuple]:
        """
        Check del match tra question e query_mapping

        :param question: Stringa per il match con query_mapping
        :return: Se trova il match ritorna il nome della tabella e la query da eseguire
        :raises HTTPException: Se la domanda non corrisponde a nessun pattern.
        """
        for pattern, (table_name, sql) in self.query_mapping.items():
            match = re.match(pattern, question)
            if match:
                return table_name, sql, match.groups()
        raise HTTPException(status_code=422, detail="Query non riconosciuta")

    def execute_query(self, question: str) -> List[Dict[str, Any]]:
        """
        Esegue la query corrispondente alla domanda e formatta il risultato.

        :param question: Domanda in linguaggio naturale
        :return: Lista di dizionari con chiavi 'item_type' e 'properties'.
        """
        table_name, sql, params = self.match_query(question)
        results, columns = self.db_manager.execute_query(sql, params)
        return self.format_response(table_name, results, columns)

    def format_response(self, table_name: str, results: Any, columns: List) -> List[Dict[str, Any]]:
        """
        Formatta i risultati della query in un formato JSON compatibile con lo script di test.

        :param table_name: Nome della tabella.
        :param results: Risultati della query come lista di tuple.
        :param columns: Nomi delle colonne della tabella.
        :return: Lista di dizionari con 'item_type' e 'properties'.
        """
        formatted_results = []
        for row in results:
            item = {
                "item_type": table_name,
                "properties": [
                    {"property_name": col, "property_value": str(value)} 
                    for col, value in zip(columns, row)
                ]
            }
            formatted_results.append(item)
        return formatted_results
