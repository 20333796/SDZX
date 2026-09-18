import logging
import signal
from time import sleep

from app.config import get_settings
from app.database import SessionLocal
from app.services.embeddings import get_embedding_provider
from app.services.ingestion import index_reviewed_documents, process_pending_documents
from app.storage import get_object_store

logger = logging.getLogger("deep_geology.worker")
running = True


def request_shutdown(*_) -> None:
    global running
    running = False


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)
    settings = get_settings()
    store = get_object_store()
    embedding_provider = get_embedding_provider(settings)
    logger.info("knowledge ingestion worker started")
    while running:
        with SessionLocal() as session:
            parsed_chunks = process_pending_documents(session, store, settings.worker_batch_size)
            indexed_chunks = index_reviewed_documents(session, embedding_provider, settings.worker_batch_size) if embedding_provider else 0
        if parsed_chunks or indexed_chunks:
            logger.info("parsed %s and indexed %s knowledge chunks", parsed_chunks, indexed_chunks)
            continue
        sleep(settings.worker_poll_seconds)
    logger.info("knowledge ingestion worker stopped")


if __name__ == "__main__":
    main()
