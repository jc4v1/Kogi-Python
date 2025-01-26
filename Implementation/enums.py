from enum import Enum

class ElementStatus(Enum):
    UNKNOWN = "unknown"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    PARTIALLY_ACTIVATED = "partially activated"
    ACHIEVED = "achieved"
    NOT_ACHIEVED = "not achieved"
    PARTIALLY_ACHIEVED = "partially achieved"
    FULFILLED = "fulfilled"
    DENIED = "denied"
    PARTIALLY_FULFILLED = "partially fulfilled"
    PARTIALLY_DENIED = "partially denied"

class LinkType(Enum):
    AND = "AND"
    OR = "OR"
    MAKE = "MAKE"
    BREAK = "BREAK"

class LinkStatus(Enum):
    UNKNOWN = "unknown"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    PARTIALLY_ACTIVATED = "partially activated"
    