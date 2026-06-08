from Semantics.enums import ElementStatus
from Semantics.goccva.pipeline import _compliance_class_from_history


def test_compliance_class_from_history_strongly_compliant() -> None:
    strong_histories = [
            (["target_a"],
            {
                "target_a": [ElementStatus.UNKNOWN, ElementStatus.SATISFIED],
            }),
            (["target_a"],
            {
                "target_a": [ElementStatus.UNKNOWN, ElementStatus.SATISFIED, ElementStatus.SATISFIED],
            }),
            (["target_a", "target_b"],
            {
                "target_a": [ElementStatus.UNKNOWN, ElementStatus.SATISFIED, ElementStatus.SATISFIED],
                "target_b": [ElementStatus.UNKNOWN, ElementStatus.SATISFIED],
            }),
    ]

    for targets, strong_history in strong_histories:
        assert _compliance_class_from_history(targets, strong_history) == "Strongly compliant"

    


def test_compliance_class_from_history_weakly_compliant() -> None:
    targets = ["target_a", "target_b"]

    weak_histories = [
            (["target_a"],
            {
                "target_a": [ElementStatus.SATISFIED,ElementStatus.UNKNOWN, ElementStatus.SATISFIED],
            }),
            (["target_a"],
            {
                "target_a": [ElementStatus.SATISFIED,ElementStatus.DENIED, ElementStatus.SATISFIED],
            }),
            (["target_a"],
            {
                "target_a": [ElementStatus.SATISFIED,ElementStatus.PENDING, ElementStatus.SATISFIED],
            }),
            (["target_a"],
            {
                "target_a": [ElementStatus.UNKNOWN, ElementStatus.SATISFIED, ElementStatus.DENIED,ElementStatus.SATISFIED],
            }),
            (["target_a"],
            {
                "target_a": [ElementStatus.UNKNOWN, ElementStatus.DENIED, ElementStatus.SATISFIED],
            }),
            (["target_a"],
            {
                "target_a": [ElementStatus.UNKNOWN, ElementStatus.PENDING, ElementStatus.SATISFIED],
            }),
            (["target_a"],
            {
                "target_a": [ElementStatus.PENDING, ElementStatus.SATISFIED],
            }),
            (["target_a", "target_b"],
            {
                "target_a": [ElementStatus.SATISFIED,ElementStatus.UNKNOWN, ElementStatus.SATISFIED, ElementStatus.SATISFIED],
                "target_b": [ElementStatus.SATISFIED,ElementStatus.DENIED, ElementStatus.SATISFIED],
            }),
    ]

    for targets, weak_history in weak_histories:
        print(f"Testing with targets: {targets} and history: {weak_history}")
        assert _compliance_class_from_history(targets, weak_history) == "Weakly compliant"


def test_compliance_class_from_history_non_compliant() -> None:
    non_histories = [
            (["target_a"],
            {
                "target_a": [ElementStatus.UNKNOWN],
            }),
            (["target_a"],
            {
                "target_a": [ElementStatus.PENDING],
            }),
            (["target_a"],
            {
                "target_a": [ElementStatus.DENIED],
            }),
            (["target_a", "target_b"],
            {
                "target_a": [ElementStatus.SATISFIED],
                "target_b": [ElementStatus.DENIED],
            }),
    ]
    
    for targets, non_history in non_histories:
        assert _compliance_class_from_history(targets, non_history) == "Non-compliant"
