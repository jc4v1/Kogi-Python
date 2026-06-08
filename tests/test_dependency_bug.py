import os
from Semantics.enums import ElementStatus
from Semantics.parsers.istar_processor import read_istar_model


def _fixture_path(name: str) -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "data", name))





def test_dependency_bug2_pending_propagates_through_refinement_chain():
    """Bug 2: When (Admin) Break breaks 'adequate declaration handling',
    pending should propagate through the dependency TO '(Employee) Money Reimbursed'
    AND further to its refinement '(Employee) Submit Declaration'."""
    model = read_istar_model(_fixture_path("dependency_bug/test0e_fail.txt"))

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

    # Step 2: Execute (Admin) Break
    model.fire_element("(Admin) Break")
    s2 = snapshot()

    # Quality that is directly broken → DENIED
    assert s2.get("adequate declaration handling") == ElementStatus.DENIED

    # Admin-side elements → PENDING
    assert s2.get("Transaction Finished") == ElementStatus.PENDING
    assert s2.get("(Admin) Money Reimbursed") == ElementStatus.PENDING

    # Dependum → PENDING (propagated via dependency link)
    assert s2.get("Money Reimbursed") == ElementStatus.PENDING

    # Employee-side elements → PENDING (propagated through dependency then refinement)
    assert s2.get("Money reimbursed") == ElementStatus.PENDING
    assert s2.get("Submit Declaration") == ElementStatus.PENDING, (
        "Submit Declaration should be PENDING via AND refinement from Money reimbursed"
    )
