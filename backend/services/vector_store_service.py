import os

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "False")
os.environ.setdefault("CHROMADB_TELEMETRY_ENABLED", "False")

import chromadb
from chromadb.config import Settings
from flask import current_app


def _disable_chroma_telemetry():
    try:
        from chromadb.telemetry.product import posthog as chroma_posthog

        def noop_capture(self, event):
            return None

        chroma_posthog.Posthog.capture = noop_capture
    except Exception:
        pass


_disable_chroma_telemetry()


class VectorStoreService:
    def __init__(self, collection_name="study_materials"):
        self.client = chromadb.PersistentClient(
            path=current_app.config["CHROMA_DIR"],
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def upsert(self, ids, documents, embeddings, metadatas):
        if not ids:
            return
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(self, embedding, top_k, where):
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def delete(self, where):
        self.collection.delete(where=where)

    def update_metadata_where(self, where, metadata):
        rows = self.collection.get(where=where, include=["documents", "embeddings", "metadatas"])
        ids = rows.get("ids") or []
        if not ids:
            return
        documents = rows.get("documents") or []
        embeddings = rows.get("embeddings") or []
        metadatas = rows.get("metadatas") or []
        updated_metadatas = [{**(item or {}), **metadata} for item in metadatas]
        self.collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=updated_metadatas)
