from Semantics.goccva.label_assignment import (
    ABSENCE,
    label_move,
    map_move,
    map_move_for_label,
)


TARGET_SETS = {
    "Declaration Handling": (
        {"Approve Declaration", "Handle Payment", "Request Payment"},
        set(),
        {"Reject Declaration", "Save Declaration"},
    ),
    "Employee Satisfaction": (
        {"Handle Payment"},
        {"Reject Declaration"},
        {"Approve Declaration", "Request Payment", "Save Declaration"},
    ),
}

ACTIVITY_MAPPING = {
    "Declaration approved": {"Approve Declaration"},
    "Payment handled": {"Handle Payment"},
    "Payment requested": {"Request Payment"},
    "Declaration rejected": {"Reject Declaration"},
    "Declaration saved": {"Save Declaration"},
}


def test_log_move_labels_make_break_and_non_related_sets() -> None:
    assert label_move(
        "Declaration Handling",
        ("Declaration approved", "Declaration approved"),
        ACTIVITY_MAPPING,
        TARGET_SETS,
    ) == "M"

    assert label_move(
        "Employee Satisfaction",
        ("Declaration rejected", "Declaration rejected"),
        ACTIVITY_MAPPING,
        TARGET_SETS,
    ) == "B"

    assert label_move(
        "Employee Satisfaction",
        ("Declaration saved", "Declaration saved"),
        ACTIVITY_MAPPING,
        TARGET_SETS,
    ) == "NR"


def test_unmapped_activity_is_not_defined() -> None:
    assert label_move(
        "Declaration Handling",
        ("Unknown activity", "Unknown activity"),
        ACTIVITY_MAPPING,
        TARGET_SETS,
    ) == "ND"


def test_model_only_move_is_labelled_for_display_but_not_for_firing() -> None:
    move = (ABSENCE, "Payment handled")

    assert map_move(ACTIVITY_MAPPING, move) == set()
    assert map_move_for_label(ACTIVITY_MAPPING, move) == {"Handle Payment"}
    assert label_move(
        "Declaration Handling",
        move,
        ACTIVITY_MAPPING,
        TARGET_SETS,
    ) == "M"


def test_model_only_move_can_be_non_related_when_it_is_in_target_alphabet() -> None:
    assert label_move(
        "Employee Satisfaction",
        (ABSENCE, "Payment requested"),
        ACTIVITY_MAPPING,
        TARGET_SETS,
    ) == "NR"
