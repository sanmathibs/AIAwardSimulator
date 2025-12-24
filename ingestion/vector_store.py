"""
Vector store interface using ChromaDB
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import config
from utils.openai_client import OpenAIClient


class VectorStore:
    """ChromaDB vector store for award clauses"""

    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        self.client = chromadb.PersistentClient(
            path=config.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )

    def create_collection(self, collection_name: str) -> Any:
        """
        Create or get a collection

        Args:
            collection_name: Unique collection name (e.g., session ID)

        Returns:
            ChromaDB collection
        """
        # Delete if exists
        try:
            self.client.delete_collection(collection_name)
        except:
            pass

        return self.client.create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def add_clauses(
        self, collection_name: str, clauses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add clauses to vector store

        Args:
            collection_name: Collection name
            clauses: List of clause dicts

        Returns:
            Dict with count and cost info
        """
        collection = self.client.get_collection(collection_name)

        # Extract texts for embedding
        texts = [f"Clause {c['clause_id']}: {c['title']}\n{c['text']}" for c in clauses]

        # Create embeddings in batches
        batch_size = 100
        all_embeddings = []
        total_cost = 0.0

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            result = self.openai_client.create_embeddings(batch)
            all_embeddings.extend(result["embeddings"])
            total_cost += result["cost"]

        # Add to collection
        ids = [f"clause_{c['metadata']['internal_id']}" for c in clauses]
        metadatas = [
            {
                "clause_id": c["clause_id"],
                "title": c["title"],
                "section": c["section"],
                **c.get("metadata", {}),
            }
            for c in clauses
        ]

        collection.add(
            ids=ids, embeddings=all_embeddings, documents=texts, metadatas=metadatas
        )

        return {"count": len(clauses), "cost": total_cost}

    def add_code_chunks(
        self, collection_name: str, chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add Python code chunks to vector store

        Args:
            collection_name: Collection name
            chunks: List of code chunk dicts with 'id', 'text', 'metadata'

        Returns:
            Dict with count and cost info
        """
        collection = self.client.get_collection(collection_name)

        # Extract texts for embedding (use code directly)
        texts = [chunk["text"] for chunk in chunks]

        # Create embeddings in batches
        batch_size = 1  # Reduced batch size for code chunks to avoid token limit
        all_embeddings = []
        total_cost = 0.0

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            result = self.openai_client.create_embeddings(batch)
            all_embeddings.extend(result["embeddings"])
            total_cost += result["cost"]

        # Add to collection
        ids = [chunk["id"] for chunk in chunks]
        # Convert list values in metadata to strings for ChromaDB compatibility
        metadatas = []
        for chunk in chunks:
            metadata = {}
            for key, value in chunk["metadata"].items():
                if isinstance(value, list):
                    metadata[key] = ",".join(str(item) for item in value)
                else:
                    metadata[key] = value
            metadatas.append(metadata)

        collection.add(
            ids=ids, embeddings=all_embeddings, documents=texts, metadatas=metadatas
        )

        return {"count": len(chunks), "cost": total_cost}

    def query(
        self, collection_name: str, query_text: str, n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query vector store for relevant clauses

        Args:
            collection_name: Collection name
            query_text: Query string
            n_results: Number of results to return

        Returns:
            List of relevant clause dicts
        """
        collection = self.client.get_collection(collection_name)

        # Embed query
        result = self.openai_client.create_embeddings([query_text])
        query_embedding = result["embeddings"][0]

        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        # Format results (handle both clauses and code chunks)
        formatted = []
        for idx in range(len(results["documents"][0])):
            metadata = results["metadatas"][0][idx]
            result_item = {
                "text": results["documents"][0][idx],
                "distance": results["distances"][0][idx],
                "metadata": metadata,
            }

            # Add clause-specific fields if available
            if "clause_id" in metadata:
                result_item["clause_id"] = metadata["clause_id"]
                result_item["title"] = metadata.get("title", "")
                result_item["section"] = metadata.get("section", "")

            formatted.append(result_item)

        return formatted

    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
        except:
            pass
