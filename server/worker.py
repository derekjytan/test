"""Interview worker scaffold. Start with Docker Compose or python -m worker."""

import logging
import math
import os
import signal
from threading import Event

logger = logging.getLogger(__name__)


def run_once() -> None:
    """Implement one iteration of background work here.

    Intentionally empty: the starter does not query or write the database,
    call the model, or change conversations. See README.md for session usage.
    """
    pass


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    poll_seconds = float(os.getenv("WORKER_POLL_SECONDS", "5"))
    if not math.isfinite(poll_seconds) or poll_seconds <= 0:
        raise ValueError("WORKER_POLL_SECONDS must be a positive finite number")

    stopped = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stopped.set())

    logger.info("Worker scaffold started; no jobs configured (poll_seconds=%s)", poll_seconds)
    while not stopped.is_set():
        try:
            run_once()
        except Exception:
            logger.exception("Worker iteration failed")
        stopped.wait(poll_seconds)
    logger.info("Worker stopped")


if __name__ == "__main__":
    main()
