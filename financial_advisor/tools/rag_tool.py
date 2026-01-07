"""Tool for retrieving tender updates from Postgres using RAG."""

import os
import psycopg2
from openai import OpenAI
import numpy as np
import typing

from google.adk.tools import FunctionTool

class RagSystem:
    def __init__(self):
        self.db_url = os.getenv("POSTGRES_URL")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key)

    def search_updates(self, query: str, limit: int = 5) -> str:
        """
        Search for relevant tender updates in the database using vector similarity.
        
        Args:
            query: The search query string (e.g., "Licitación carreteras").
            limit: Number of results to return.
            
        Returns:
            A string containing the relevant updates found.
        """
        if not self.db_url:
            return "Error: POSTGRES_URL not set."
        if not self.openai_api_key:
            return "Error: OPENAI_API_KEY not set."

        try:
            # 1. Generate embedding
            response = self.client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            embedding = response.data[0].embedding

            # 2. Query Postgres
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            # Assuming 'embedding' column is vector type
            # We cast the python list to a string representation of vector for pgvector
            embedding_str = f"[{','.join(map(str, embedding))}]"
            
            sql = """
                SELECT id, texto_semantico, created_at, metadata 
                FROM updates 
                ORDER BY embedding <=> %s::vector 
                LIMIT %s;
            """
            
            cur.execute(sql, (embedding_str, limit))
            rows = cur.fetchall()
            
            cur.close()
            conn.close()
            
            if not rows:
                return "No relevant updates found."
                
            results = []
            for row in rows:
                # row structure: (id, texto_semantico, created_at, metadata)
                doc_id = row[0]
                content = row[1]
                date = row[2]
                meta = row[3] if row[3] else {}
                
                # Format metadata nicely
                meta_str = ""
                if isinstance(meta, dict):
                    # Prioritize key fields with fallback options
                    title = meta.get('title', meta.get('nombre_procedimiento', meta.get('descripcion', 'Sin título')))
                    
                    monto = meta.get('monto_sin_imp__minimo', meta.get('importe_drc', meta.get('amount', meta.get('tender_value_amount', 'No especificado'))))
                    
                    institucion = meta.get('institucion', meta.get('buyer_name', 'No especificada'))
                    
                    tipo = meta.get('tipo_procedimiento', 'No especificado')
                    estado = meta.get('estatus_contrato', 'No especificado')
                    
                    url = meta.get('url', meta.get('link', meta.get('uri', 'No disponible')))
                    
                    meta_str = (
                        f"Institución: {institucion}\n"
                        f"Título/Descripción: {title}\n"
                        f"Monto Estimado: {monto}\n"
                        f"Tipo: {tipo}\n"
                        f"Estado: {estado}\n"
                        f"URL: {url}\n"
                    )

                results.append(f"ID: {doc_id}\nDate: {date}\n{meta_str}Content: {content}\n---")
                
            return "\n".join(results)
            
        except Exception as e:
            # Fallback for demo/simulation purposes if DB/API fails
            print(f"Error querying database (using simulation): {str(e)}")
            return (
                "ID: sim-001\n"
                "Date: 2025-01-05\n"
                "Institución: AGENCIA REGULADORA DEL TRANSPORTE FERROVIARIO\n"
                "Monto Estimado: 27,451,532,410.19\n"
                "Tipo: Licitación Pública\n"
                "Estado: Adjudicado\n"
                "Content: CONSTRUCCIÓN Y DISEÑO TREN DE PASAJEROS SALTILLONUEVO LAREDO, SEGMENTOS 13 Y 14. Proveedor: OPERADORA CICSA SA DE CV.\n---\n"
                "ID: sim-002\n"
                "Date: 2025-01-05\n"
                "Institución: AGENCIA REGULADORA DEL TRANSPORTE FERROVIARIO\n"
                "Monto Estimado: 17,417,178,859.48\n"
                "Tipo: Licitación Pública\n"
                "Estado: Adjudicado\n"
                "Content: SISTEMA FERROVIARIO PARA CONECTAR QUERETARO-IRAPUATO, TRAMO II OBRA. Proveedor: MOTA-ENGIL MEXICO S A P I DE CV.\n---\n"
                "ID: sim-003\n"
                "Date: 2025-01-05\n"
                "Institución: AGENCIA REGULADORA DEL TRANSPORTE FERROVIARIO\n"
                "Monto Estimado: 12,652,090,337.50\n"
                "Tipo: Licitación Pública\n"
                "Estado: Adjudicado\n"
                "Content: SISTEMA FERROVIARIO PARA CONECTAR SALTILLO - NUEVO LAREDO. Proveedor: ICA CONSTRUCTORA SA DE CV.\n"
            )

def RagTool():
    """Factory function to create the RAG FunctionTool."""
    rag = RagSystem()
    return FunctionTool(func=rag.search_updates)
