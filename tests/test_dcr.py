import os
from Semantics.dcr import load_dcr_as_ts


def test_load_dcr_ts():
    path = os.path.join(os.path.dirname(__file__), '..', 'Data', 'example2', 'dcr.xml')
    path = os.path.normpath(path)
    ts = load_dcr_as_ts(path)
    # initial state should be part of states
    assert ts.initial_state() in ts.states()
    nstates, ntrans = ts.size()
    assert nstates >= 1
    # there's at least one enabled transition in the initial marking for this model
    enabled = ts.get_enabled_actions(ts.initial_state())
    assert len(enabled) >= 1
