from enum import Enum

class ElementStatus(Enum):
    UNKNOWN = "unknown"      # initial state
    SATISFIED = "satisfied"  # satisfied/achieved
    PENDING = "pending"      # executed pending
    DENIED = "denied"        # denied

class LinkType(Enum):
    AND = "AND"
    OR = "OR"
    MAKE = "MAKE"
    BREAK = "BREAK"
    DEPENDENCY = "DEPENDENCY"

class ComplianceStatus(str, Enum):
    STRONGLY_COMPLIANT = "Strongly compliant"
    WEAKLY_COMPLIANT = "Weakly compliant"
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-compliant"