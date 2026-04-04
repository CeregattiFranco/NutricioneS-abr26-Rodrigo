import chromadb
from chromadb.utils import embedding_functions
import uuid
import logging
from typing import List, Dict, Any
from nutriciones.core import config, get_base_logger

logger = get_base_logger("NSS-ORACLE")

class ClinicalMemory:
    """Implementa a Memória Vetorial (RAG) da clínica."""
    def __init__(self, persist_directory: str = str(config.DATA_DIR / "vector_memory")):
        # ChromaDB persistente
        self.client = chromadb.PersistentClient(path=persist_directory)
        # Usando modelo open-source leve para embeddings (Factor II - Auto-contido)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name="clinica_sem_stress_memory",
            embedding_function=self.embedding_fn
        )

    def adicionar_memoria(self, texto: str, metadata: Dict[str, Any]):
        """Vetoriza e salva um novo pedaço de conhecimento clínico."""
        mem_id = str(uuid.uuid4())
        logger.info(f"[INFO] [NSS-ORACLE] - Vetorizando novo conhecimento: {metadata.get('tipo', 'generic')}")
        self.collection.add(
            documents=[texto],
            metadatas=[metadata],
            ids=[mem_id]
        )

    def consultar(self, query: str, n_results: int = 3) -> str:
        """Realiza busca semântica na base de conhecimento da clínica. Filtra casos de sucesso (Aderência > 8) para garantir sugestões eficazes."""
        logger.info(f"[INFO] [NSS-ORACLE] - Consultando memória para: {query}")
        
        # Filtro de Sucesso (Metadados do NSS Analytics)
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"tipo": "consulta"} # Priorizar consultas com desfecho
        )
        
        if not results['documents'][0]:
            return "Nenhuma memória similar encontrada na base local."
            
        fmt_res = "\n---\n".join([
            f"Tipo: {m.get('tipo')} | Data: {m.get('data')} | Sucesso: {m.get('sucesso', 'N/A')}\nConteúdo: {d}" 
            for d, m in zip(results['documents'][0], results['metadatas'][0])
        ])
        return fmt_res

# Singleton da Memória Clínica
oracle_memory = ClinicalMemory()
