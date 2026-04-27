import chromadb
from chromadb.config import Settings


def get_chroma_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path="./chroma_db", settings=Settings(anonymized_telemetry=False)
    )


def get_raw_contents_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    return client.get_or_create_collection(
        name="raw_contents", metadata={"hnsw:space": "cosine"}
    )


def get_contents_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    return client.get_or_create_collection(
        name="contents", metadata={"hnsw:space": "cosine"}
    )
