import logging
from threading import Lock
from brain.triggers.base_trigger import BaseTrigger

logger = logging.getLogger(__name__)


class TriggerScheduler:
    def __init__(self):
        self.triggers = []
        self._lock = Lock()

    def add_trigger(self, trigger: BaseTrigger):
        """
        Add a trigger to the scheduler.
        :param trigger: A BaseTrigger instance (TimeTrigger, EventTrigger, etc.)
        """
        with self._lock:
            # Prevent duplicate triggers with the same prompt and type
            for existing in self.triggers:
                if (type(existing) == type(trigger) and
                    existing.prompt == trigger.prompt and
                    not existing.executed):
                    logger.warning(f"Duplicate trigger: {trigger.prompt}")
                    return existing

            self.triggers.append(trigger)
            logger.info(f"Trigger added: {trigger}")
            return trigger

    def get_due_triggers(self):
        """
        Get all triggers that are ready to execute.
        Each trigger decides if it's ready based on its own logic.
        Only returns triggers that are claimed successfully to prevent double processing.
        """
        due = []
        with self._lock:
            for trigger in self.triggers:
                if trigger.is_due() and trigger.try_claim():
                    due.append(trigger)

        return due

    def mark_trigger_executed(self, trigger: BaseTrigger):
        """
        Mark a trigger as executed after it has been processed.
        """
        with self._lock:
            trigger.mark_executed()

    def cleanup_executed_triggers(self):
        """
        Remove all executed triggers from the scheduler.
        Call this periodically to prevent memory leaks.
        """
        with self._lock:
            self.triggers = [t for t in self.triggers if not t.executed]

    def list_triggers(self):
        """
        Return a list of all triggers (executed and pending).
        """
        with self._lock:
            return list(self.triggers)

    def delete_trigger(self, trigger_id: str) -> bool:
        """
        Delete a trigger by its ID.
        Returns True if the trigger was found and deleted, False otherwise.
        """
        with self._lock:
            for i, trigger in enumerate(self.triggers):
                if trigger.id == trigger_id:
                    self.triggers.pop(i)
                    logger.info(f"Trigger deleted: {trigger_id}")
                    return True
            logger.warning(f"Trigger not found: {trigger_id}")
            return False

# Global instance for shared access across the core and tools
scheduler = TriggerScheduler()


