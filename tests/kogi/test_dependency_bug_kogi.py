import os
from Semantics.enums import ElementStatus
from Semantics.parsers.istar_processor import read_istar_model


def _fixture_path(name: str) -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "data", name))


def test_dependency_bug1_no_pending_across_dependency_on_employee_break():
    """Bug 1: When (Employee) Break breaks 'Increase employee satisfaction',
    the dependum 'Money Reimbursed' and depender '(Admin) Money Reimbursed'
    should stay SATISFIED. Pending status should NOT propagate across the dependency."""
    model = read_istar_model(_fixture_path("dependency_bug/test0e_fail.txt"))
    model.kogi = True

    def snapshot():
        s = {}
        for t in model.tasks:
            s[t] = model.get_element_status(t)
        for g in model.goals:
            s[g] = model.get_element_status(g)
        for q in model.qualities:
            s[q] = model.get_quality_status(q)
        return s

    # Step 1: Execute Submit Declaration → everything satisfied
    model.fire_element("Submit Declaration")
    s1 = snapshot()
    assert s1.get("Submit Declaration") == ElementStatus.SATISFIED
    assert s1.get("Money reimbursed") == ElementStatus.SATISFIED
    assert s1.get("Increase employee satisfaction") == ElementStatus.SATISFIED
    assert s1.get("Money Reimbursed") == ElementStatus.SATISFIED
    assert s1.get("(Admin) Money Reimbursed") == ElementStatus.SATISFIED
    assert s1.get("Transaction Finished") == ElementStatus.SATISFIED
    assert s1.get("adequate declaration handling") == ElementStatus.SATISFIED
    assert s1.get("(Employee) Break") == ElementStatus.UNKNOWN
    assert s1.get("(Admin) Break") == ElementStatus.UNKNOWN

    # Step 2: Execute (Employee) Break
    model.fire_element("(Employee) Break")
    s2 = snapshot()

    # Quality that is directly broken → DENIED
    assert s2.get("Increase employee satisfaction") == ElementStatus.DENIED

    # Employee-side elements → PENDING
    assert s2.get("Money reimbursed") == ElementStatus.PENDING
    assert s2.get("Submit Declaration") == ElementStatus.PENDING

    # Dependency and Admin-side elements should STAY SATISFIED (this is Bug 1)
    assert s2.get("Money Reimbursed") == ElementStatus.SATISFIED, (
        "Dependum should stay SATISFIED, not propagate across dependency"
    )
    assert s2.get("(Admin) Money Reimbursed") == ElementStatus.SATISFIED, (
        "Depender should stay SATISFIED, not propagate across dependency"
    )
    assert s2.get("Transaction Finished") == ElementStatus.SATISFIED
    assert s2.get("adequate declaration handling") == ElementStatus.SATISFIED
