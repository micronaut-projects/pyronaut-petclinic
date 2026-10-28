"""Duration normalization at the Java/Python boundary."""

from datetime import timedelta


def duration_minutes(value) -> int:
    """GraalPy exposes Java durations as Python timedeltas when loading entities."""

    if isinstance(value, timedelta):
        return value // timedelta(minutes=1)
    return value.toMinutes()
