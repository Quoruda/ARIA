from datetime import datetime, timedelta
import logging
from triggers.base_trigger import BaseTrigger

logger = logging.getLogger(__name__)


class TimeTrigger(BaseTrigger):
    """
    Trigger based on scheduled time (absolute or relative).
    Executes when the current time reaches or passes the scheduled time.
    """

    def __init__(self, scheduled_time: datetime, prompt: str, context: str = None):
        super().__init__(prompt, context)
        self.scheduled_time = scheduled_time

    def is_due(self) -> bool:
        """Check if the scheduled time has been reached."""
        with self._lock:
            if self.executed:
                return False

            now = datetime.now()
            time_window = timedelta(seconds=60)
            if self.scheduled_time <= now < self.scheduled_time + time_window:
                logger.info(f"TimeTrigger due: {self.prompt}")
                return True

        return False

    def mark_executed(self):
        # Override to keep lock discipline
        with self._lock:
            self.executed = True
            self._claimed = False

    def __repr__(self):
        return f"<TimeTrigger(time={self.scheduled_time.strftime('%H:%M:%S')}, prompt='{self.prompt[:20]}...', executed={self.executed})>"
