import os

import chromadb

CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_store")

_client = chromadb.PersistentClient(path=CHROMA_PATH)

SOP_COLLECTION_NAME = "sop_knowledge"


def get_sop_collection():
    """Single collection holding both static SOP chunks and operator notes,
    distinguished by metadata['type'] ('sop' vs 'operator_note')."""
    return _client.get_or_create_collection(SOP_COLLECTION_NAME)
