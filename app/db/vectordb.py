import chromadb
from chromadb.config import Settings
from app.config import settings as app_settings


def get_chroma_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=app_settings.chroma_db_path, settings=Settings(anonymized_telemetry=False)
    )


def get_raw_contents_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    return client.get_or_create_collection(
        name="raw_contents", metadata={"hnsw:space": "cosine"}
    )


def get_contents_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    return client.get_or_create_collection(
        name="contents", metadata={"hnsw:space": "cosine"}
    )
