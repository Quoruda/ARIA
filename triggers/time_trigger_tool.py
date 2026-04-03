"""
Time-based trigger tools.
These tools are specific to scheduling actions at specific times or delays.
"""

import logging
from datetime import datetime, timedelta
import re
from triggers.scheduler import scheduler
from triggers.time_trigger import TimeTrigger

logger = logging.getLogger(__name__)


def schedule_at_time(time_str: str, action_prompt: str, context: str = None):
    """
    Schedule an action at a specific absolute time (HH:MM format).

    :param time_str: Time in HH:MM format (e.g., '14:30', '09:00')
    :param action_prompt: The instruction for the AI to follow
    :param context: Optional context for the trigger
    :return: Confirmation message
    """
    now = datetime.now()

    match = re.match(r'(\d{1,2}):(\d{2})', time_str)
    if not match:
        return f"❌ Invalid format. Use HH:MM (e.g., 14:30)"

    hour = int(match.group(1))
    minute = int(match.group(2))

    if not (0 <= hour < 24 and 0 <= minute < 60):
        return f"❌ Invalid time: {hour}:{minute:02d}. Use HH:MM format (00:00 - 23:59)."

    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If target time is in the past, schedule for tomorrow
    if target_time <= now:
        target_time += timedelta(days=1)

    trigger = TimeTrigger(target_time, action_prompt, context)
    scheduler.add_trigger(trigger)

    logger.info(f"Trigger scheduled for {target_time.strftime('%H:%M:%S')}: {action_prompt}")
    return f"✅ Trigger scheduled for {target_time.strftime('%H:%M:%S')}: {action_prompt}"


def schedule_in_delay(delay_str: str, action_prompt: str, context: str = None):
    """
    Schedule an action after a specific delay.

    :param delay_str: Delay string (e.g., '+10m' for 10 minutes, '+2h' for 2 hours)
    :param action_prompt: The instruction for the AI to follow
    :param context: Optional context for the trigger
    :return: Confirmation message
    """
    now = datetime.now()

    match = re.match(r'\+(\d+)([mh])', delay_str)
    if not match:
        return f"❌ Invalid format. Use +Xm (minutes) or +Xh (hours) (e.g., +10m, +2h)"

    value = int(match.group(1))
    unit = match.group(2)

    if unit == 'm':
        target_time = now + timedelta(minutes=value)
    elif unit == 'h':
        target_time = now + timedelta(hours=value)
    else:
        return f"❌ Invalid unit. Use 'm' (minutes) or 'h' (hours)."

    if not action_prompt or not action_prompt.strip():
        return "❌ Action prompt cannot be empty."

    trigger = TimeTrigger(target_time, action_prompt, context)
    scheduler.add_trigger(trigger)

    logger.info(f"Trigger scheduled in {value}{'m' if unit == 'm' else 'h'}: {action_prompt}")
    return f"✅ Trigger scheduled in {value}{'m' if unit == 'm' else 'h'}: {action_prompt}"

