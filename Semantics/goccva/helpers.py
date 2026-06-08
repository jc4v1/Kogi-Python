import json
import random
import re
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd
from pm4py.objects.petri_net.obj import PetriNet as Pm4pyPetriNet, Marking
from pm4py.algo.simulation.playout.petri_net import algorithm as simulator
from pm4py.objects.log.obj import EventLog, Trace, Event

from Semantics.goal_model import GoalModel
from Semantics.petri_net import PetriNet as SemanticsPetriNet
from Semantics.goccva.pipeline import ABSENCE

def normalize(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def similarity(a: str, b: str) -> float:
    na, nb = normalize(a), normalize(b)
    if na == nb:
        return 1.0
    set_a, set_b = set(na.split()), set(nb.split())
    jaccard = len(set_a & set_b) / max(1, len(set_a | set_b))
    seq = SequenceMatcher(None, na, nb).ratio()
    return max(jaccard, seq)


def propose_activity_vocab(gm: GoalModel) -> List[str]:
    # Process-facing labels inferred from task names.
    task_names = list(gm.leaves())
    return sorted(task_names)


def propose_mapping(gm: GoalModel, activity_labels: Iterable[str], threshold: float = 0.55) -> Dict[str, Set[str]]:
    leafs = list(gm.leaves())
    mapping: Dict[str, Set[str]] = {}
    for act in activity_labels:
        scored = sorted(((leaf, similarity(act, leaf)) for leaf in leafs), key=lambda x: x[1], reverse=True)
        best_score = scored[0][1] if scored else 0.0
        assigned = {leaf for leaf, s in scored if s == best_score and s >= threshold}
        mapping[act] = assigned
    return mapping


def simulate_clean_log(net: Pm4pyPetriNet, im: Marking, num_traces: int = 20, seed: int = 7) -> EventLog:
    random.seed(seed)
    params = {
        simulator.Variants.BASIC_PLAYOUT.value.Parameters.NO_TRACES: num_traces,
        simulator.Variants.BASIC_PLAYOUT.value.Parameters.MAX_TRACE_LENGTH: 10,
    }
    return simulator.apply(net, im, variant=simulator.Variants.BASIC_PLAYOUT, parameters=params)


def clone_trace_with_noise(trace: Trace, vocab: List[str], noise_prob: float = 0.35) -> Trace:
    events = [ev['concept:name'] for ev in trace]
    noisy = list(events)
    actions = []
    if random.random() < noise_prob:
        actions.append(random.choice(['insert_unknown', 'delete', 'swap', 'replace']))
    if random.random() < noise_prob / 2:
        actions.append(random.choice(['insert_unknown', 'delete', 'swap']))

    for act in actions:
        if act == 'insert_unknown':
            pos = random.randint(0, len(noisy))
            noisy.insert(pos, 'Manual accessibility check')
        elif act == 'delete' and noisy:
            pos = random.randrange(len(noisy))
            del noisy[pos]
        elif act == 'swap' and len(noisy) >= 2:
            i = random.randrange(len(noisy) - 1)
            noisy[i], noisy[i+1] = noisy[i+1], noisy[i]
        elif act == 'replace' and noisy:
            pos = random.randrange(len(noisy))
            choices = [x for x in vocab if x != noisy[pos]] + ['Manual accessibility check']
            noisy[pos] = random.choice(choices)

    new_trace = Trace(attributes=dict(trace.attributes))
    for idx, act in enumerate(noisy):
        ev = Event({'concept:name': act, 'time:timestamp': pd.Timestamp('2026-01-01') + pd.Timedelta(seconds=idx)})
        new_trace.append(ev)
    return new_trace


def inject_noise(log: EventLog, vocab: List[str], noise_fraction: float = 0.4, seed: int = 11) -> EventLog:
    random.seed(seed)
    out = EventLog()
    for trace in log:
        if random.random() < noise_fraction:
            out.append(clone_trace_with_noise(trace, vocab=vocab))
        else:
            out.append(clone_trace_with_noise(trace, vocab=vocab, noise_prob=0.0))
    return out


def _short_alignment(alignment: List[Tuple[Optional[str], Optional[str]]], limit: int = 6) -> str:
    rendered = []
    for model_move, log_move in alignment[:limit]:
        left = model_move if model_move is not None else ABSENCE
        right = log_move if log_move is not None else ABSENCE
        rendered.append(f"({left} -> {right})")
    if len(alignment) > limit:
        rendered.append("...")
    return " ".join(rendered)


def format_alignment_results(alignment_results: List[dict], noisy_log: EventLog) -> str:
    header = [
        "=== PM4PY Alignment Results ===",
        f"traces: {len(alignment_results)}",
        "",
    ]
    lines = []
    for idx, (trace, al_res) in enumerate(zip(noisy_log, alignment_results), start=1):
        trace_labels = [e['concept:name'] for e in trace]
        alignment = al_res.get('alignment', [])
        lines.extend(
            [
                f"Trace {idx}",
                f"  fitness: {al_res.get('fitness')} | cost: {al_res.get('cost')}",
                f"  events: {' | '.join(trace_labels)}",
                f"  alignment: {_short_alignment(alignment)}",
                "",
            ]
        )
    return "\n".join(header + lines).rstrip()


def event_log_to_sequences(log: EventLog) -> List[List[str]]:
    return [[e['concept:name'] for e in tr] for tr in log]


def sequences_to_event_log(sequences: List[List[str]]) -> EventLog:
    log = EventLog()
    for trace_labels in sequences:
        trace = Trace()
        for idx, act in enumerate(trace_labels):
            ev = Event({'concept:name': act, 'time:timestamp': pd.Timestamp('2026-01-01') + pd.Timedelta(seconds=idx)})
            trace.append(ev)
        log.append(trace)
    return log


def save_logs(clean_log: EventLog, noisy_log: EventLog, logs_path: str) -> str:
    payload = {
        'clean_log': event_log_to_sequences(clean_log),
        'noisy_log': event_log_to_sequences(noisy_log),
    }
    with open(logs_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    return logs_path


def load_logs(logs_path: str) -> Tuple[EventLog, EventLog]:
    with open(logs_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    clean_sequences = payload.get('clean_log', [])
    noisy_sequences = payload.get('noisy_log', [])
    clean_log = sequences_to_event_log(clean_sequences)
    noisy_log = sequences_to_event_log(noisy_sequences)
    return clean_log, noisy_log


def create_event_log(
    petri_net: SemanticsPetriNet,
    num_traces: int = 18,
    noise_fraction: float = 0.55) -> Tuple[EventLog, EventLog]:
    vocab = [t.label for t in petri_net.net.transitions if t.label is not None]
    clean_log = simulate_clean_log(petri_net.net, petri_net.init, num_traces=num_traces)
    noisy_log = inject_noise(clean_log, vocab=vocab, noise_fraction=noise_fraction)
    return clean_log, noisy_log


def prepare_reproducible_logs(
    petri_net: SemanticsPetriNet,
    logs_path: str = 'content/goccva_logs.json',
    num_traces: int = 18,
    noise_fraction: float = 0.55) -> str:
    clean_log, noisy_log = create_event_log(
        petri_net,
        num_traces=num_traces,
        noise_fraction=noise_fraction)
    return save_logs(clean_log, noisy_log, logs_path)
