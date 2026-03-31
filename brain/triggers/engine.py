import logging
import threading
import time
from typing import Callable

from brain.triggers.scheduler import scheduler

logger = logging.getLogger(__name__)


class TriggerEngine:
    """Background engine that polls the scheduler and dispatches due triggers.

    It is decoupled from CoreManager and only depends on two callbacks:
    - is_busy(): tells if the system can process a new trigger
    - process_prompt(prompt: str): actually handles the prompt (user or trigger)
    """

    def __init__(self, is_busy: Callable[[], bool], process_prompt: Callable[[str], None],
                 check_interval: float = 2.0, max_wait: float = 30.0):
        self._is_busy = is_busy
        self._process_prompt = process_prompt
        self._check_interval = check_interval
        self._max_wait = max_wait
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        if not self._thread.is_alive():
            logger.info("Starting TriggerEngine thread")
            self._thread.start()

    def stop(self):
        logger.info("Stopping TriggerEngine thread")
        self._stop_event.set()

    def _loop(self):
        cleanup_counter = 0
        while not self._stop_event.is_set():
            due_triggers = scheduler.get_due_triggers()
            for trigger in due_triggers:
                waited = 0.0
                # Wait for system availability with timeout
                while self._is_busy() and waited < self._max_wait and not self._stop_event.is_set():
                    time.sleep(1.0)
                    waited += 1.0

                if waited >= self._max_wait:
                    logger.warning(
                        f"Trigger timeout: system was busy for {self._max_wait}s, processing anyway"
                    )

                full_prompt = trigger.prompt
                if getattr(trigger, "context", None):
                    full_prompt = f"[CONTEXT: {trigger.context}] {trigger.prompt}"

                try:
                    self._process_prompt(full_prompt)
                except Exception:
                    logger.exception("Error while processing trigger prompt")

                # Mark as executed only after dispatching processing
                scheduler.mark_trigger_executed(trigger)

                # Small gap to avoid hammering multiple triggers
                time.sleep(0.1)

            cleanup_counter += 1
            if cleanup_counter >= 10:
                scheduler.cleanup_executed_triggers()
                cleanup_counter = 0

            time.sleep(self._check_interval)



