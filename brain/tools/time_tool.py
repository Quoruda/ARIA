from datetime import datetime

def get_temporal_context():
    """Returns the current time with the date in a human-readable format."""
    return datetime.now().strftime("%A %d %B %Y %H:%M")
