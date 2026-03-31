"""
Generic trigger management tools.
Specialized trigger types (time-based, event-based, etc.) have their own tool files.
"""

import logging
from brain.triggers.scheduler import scheduler

logger = logging.getLogger(__name__)


# ============================================================================
# Generic Trigger Management Tools
# ============================================================================

def list_all_triggers():
    """
    List all scheduled triggers in a format suitable for AI processing.
    Returns a structured dict with trigger information for deletion/verification.
    """
    triggers = scheduler.list_triggers()

    if not triggers:
        return {
            "success": True,
            "count": 0,
            "triggers": []
        }

    trigger_list = []
    for trigger in triggers:
        status = "executed" if trigger.executed else "pending"
        trigger_type = trigger.__class__.__name__

        trigger_info = {
            "id": trigger.id,
            "type": trigger_type,
            "status": status,
            "prompt": trigger.prompt,
            "context": trigger.context if trigger.context else None,
        }

        # Add type-specific details
        if hasattr(trigger, 'scheduled_time'):
            trigger_info["scheduled_time"] = trigger.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')

        trigger_list.append(trigger_info)

    return {
        "success": True,
        "count": len(trigger_list),
        "triggers": trigger_list
    }


def delete_trigger(trigger_id: str):
    """
    Delete a trigger by its ID.
    Returns a confirmation message.
    """
    if scheduler.delete_trigger(trigger_id):
        return f"✅ Trigger {trigger_id} deleted successfully."
    else:
        return f"❌ Trigger {trigger_id} not found."


def delete_triggers_by_prompt(prompt_substring: str):
    """
    Delete all triggers whose prompt contains the given substring.
    Returns a confirmation message with count.
    """
    triggers = scheduler.list_triggers()
    deleted_count = 0

    for trigger in triggers:
        if prompt_substring.lower() in trigger.prompt.lower():
            if scheduler.delete_trigger(trigger.id):
                deleted_count += 1

    if deleted_count == 0:
        return f"ℹ️ No triggers matching '{prompt_substring}' found."

    return f"✅ {deleted_count} trigger(s) deleted."



