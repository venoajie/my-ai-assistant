# src/ai_assistant/reranker.py

from typing import List
import structlog

from .config import ai_settings

logger = structlog.get_logger(__name__)

# A simple singleton pattern to ensure we only load the model once.
_reranker_instance = None

class Reranker:
    """
    A wrapper for a sentence-transformers CrossEncoder model to rerank documents.
    This class is designed as a singleton to prevent re-loading the model.
    """
    def __init__(self):
        self.model = None
        self.model_name = ai_settings.rag.reranker_model_name
        
        try:
            from sentence_transformers.cross_encoder import CrossEncoder
            logger.info("Loading reranker model...", model_name=self.model_name)
            self.model = CrossEncoder(self.model_name)
            logger.info("Reranker model loaded successfully.")
        except ImportError:
            logger.error(
                "sentence-transformers is not installed. Reranking is disabled.",
                suggestion="Install the project with 'pip install .[client]' or 'pip install .[indexing]'"
            )
            raise
        except Exception as e:
            logger.error("Failed to load the reranker model.", error=str(e))
            raise

    def rerank(self, query: str, documents: List[str]) -> List[str]:
        """
        Reranks a list of documents based on their relevance to a query.

        Args:
            query: The user's search query.
            documents: A list of document strings retrieved from the vector store.

        Returns:
            A sorted list of document strings, from most to least relevant.
        """
        if not self.model:
            logger.warning("Reranker model not loaded. Returning original document order.")
            return documents
            
        if not documents:
            return []

        logger.info("Reranking documents...", query=query, count=len(documents))
        
        # The CrossEncoder expects pairs of [query, document]
        query_doc_pairs = [[query, doc] for doc in documents]
        
        # Predict scores for each pair
        scores = self.model.predict(query_doc_pairs, show_progress_bar=False)
        
        # Combine documents with their scores and sort in descending order
        doc_score_pairs = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        
        # Return just the sorted documents
        sorted_documents = [doc for doc, score in doc_score_pairs]
        
        return sorted_documents

def get_reranker() -> Reranker:
    """Factory function to get the singleton Reranker instance."""
    global _reranker_instance
    if _reranker_instance is None:
        try:
            _reranker_instance = Reranker()
        except Exception:
            # If initialization fails, we keep the instance as None
            # so the application can proceed without reranking.
            _reranker_instance = None
    return _reranker_instance
