from collections import Counter
from itertools import combinations
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from pm4py.objects.log.obj import EventLog

from Semantics.enums import ComplianceStatus, ElementStatus
from Semantics.goal_model import GoalModel
from Semantics.goccva.label_assignment import ABSENCE, label_move, map_move
from Semantics.petri_net import PetriNet as SemanticsPetriNet
from Semantics.goccva.target_sets import compute_target_sets, target_sets_as_rows


def compute_goal_oriented_alignment(
    gm: GoalModel,
    alignment: List[Sequence[str]],
    activity_mapping: Dict[str, Set[str]],
    targets: List[str],
    initial_marking: Optional[Dict[str, ElementStatus]] = None,
) -> Tuple[List[dict], Dict[str, str], str]:
    gm.reset()
    if initial_marking:
        gm.set_markings(initial_marking)

    target_sets = compute_target_sets(gm, targets)
    go_alignment = []
    status_history = {t: [] for t in targets}

    for move in alignment:
        mapped = map_move(activity_mapping, move)
        # print(f"Move: {move} -> Mapped: {mapped}")
        if mapped:
            gm.fire_elements(mapped)
        marking = gm.get_markings()

        theta = []
        for t in targets:
            lab = label_move(t, move, activity_mapping, target_sets)
            theta.append({'target': t, 'label': lab, 'status': marking[t].value if hasattr(marking[t], 'value') else marking[t]})
            status_history[t].append(marking[t])
        go_alignment.append({'move': move, 'mapped_tasks': sorted(mapped), 'theta': theta})

    comp_class = _compliance_class_from_history(targets, status_history)
    return go_alignment, marking, comp_class

def _compliance_class_from_history(
    targets: Sequence[str],
    status_history: Dict[str, List[ElementStatus]],
) -> str:
    weak = all(status_history[t] and status_history[t][-1] == ElementStatus.SATISFIED for t in targets)
    stable = True
    for t in targets:
        seen_sat = False
        for s in status_history[t]:
            if s == ElementStatus.SATISFIED:
                seen_sat = True
            elif not seen_sat and s in {ElementStatus.PENDING, ElementStatus.DENIED}:
                stable = False
                break
            elif seen_sat and s != ElementStatus.SATISFIED:
                stable = False
                break
    comp_class = ComplianceStatus.NON_COMPLIANT.value
    if weak:
        comp_class = ComplianceStatus.STRONGLY_COMPLIANT.value if stable else ComplianceStatus.WEAKLY_COMPLIANT.value
    return comp_class


def _class_key(value: str) -> str:
    return str(value).strip().lower().replace('_', '-').replace(' ', '-')


def sort_summary(summary: List[dict]) -> List[dict]:
    traditional_rank = {
        'optimal': 0,
        'non-optimal': 1,
    }
    goal_rank = {
        'strongly-compliant': 0,
        'strogly-compliant': 0,
        'weakly-compliant': 1,
        'non-compliant': 2,
    }

    def key(row: dict) -> tuple:
        traditional = traditional_rank.get(_class_key(row.get('traditional_class', '')), 99)
        goal = goal_rank.get(_class_key(row.get('goal_class', '')), 99)
        trace_id = row.get('trace_id', 0)
        return traditional, goal, trace_id

    return sorted(summary, key=key)


def analyse(
    goal_model: GoalModel,
    petri_net: SemanticsPetriNet,
    noisy_log: EventLog,
    targets: List[str],
    activity_mapping: Dict[str, Set[str]],
    initial_marking: Optional[Dict[str, ElementStatus]] = None,
):
    gm = goal_model
    activity_mapping = gm.canonicalize_activity_mapping(activity_mapping)

    alignment_results = petri_net.apply_log_alignments(noisy_log)

    summary = []
    detailed = []
    for idx, (trace, al_res) in enumerate(zip(noisy_log, alignment_results), start=1):
        alignment = [(a if a is not None else ABSENCE, b if b is not None else ABSENCE) for a, b in al_res['alignment']]
        go_alignment, final_marking, comp_class = compute_goal_oriented_alignment(
            gm,
            alignment,
            activity_mapping,
            targets,
            initial_marking=initial_marking,
        )
        trace_labels = [e['concept:name'] for e in trace]
        alignment_cost = al_res.get('cost')
        fitness = al_res.get('fitness')
        traditional_class = 'optimal' if alignment_cost == 0 or fitness == 1 else 'non-optimal'
        summary.append({
            'trace_id': idx,
            'trace': ' | '.join(trace_labels),
            'alignment_cost': alignment_cost,
            'fitness': fitness,
            'traditional_class': traditional_class,
            'goal_class': comp_class,
        })
        detailed.append({
            'trace_id': idx,
            'trace': trace_labels,
            'pm4py_alignment': alignment,
            'goal_oriented_alignment': go_alignment,
            'final_marking': {k: v.value if hasattr(v, 'value') else v for k, v in final_marking.items()},
            'targets': targets,
        })
    target_rows = target_sets_as_rows(compute_target_sets(gm, targets))

    return sort_summary(summary), detailed, target_rows


def analyse_no_pm(
    goal_model: GoalModel,
    event_log: EventLog,
    targets: List[str],
    activity_mapping: Dict[str, Set[str]],
    initial_marking: Optional[Dict[str, ElementStatus]] = None,
):
    gm = goal_model
    activity_mapping = gm.canonicalize_activity_mapping(activity_mapping)

    summary = []
    detailed = []
    for idx, trace in enumerate(event_log, start=1):
        trace_labels = [event['concept:name'] for event in trace]
        trace_alignment = [(activity,) for activity in trace_labels]
        go_alignment, final_marking, comp_class = compute_goal_oriented_alignment(
            gm,
            trace_alignment,
            activity_mapping,
            targets,
            initial_marking=initial_marking,
        )

        summary.append({
            'trace_id': idx,
            'trace': ' | '.join(trace_labels),
            'goal_class': comp_class,
        })
        detailed.append({
            'trace_id': idx,
            'trace': trace_labels,
            'goal_oriented_alignment': go_alignment,
            'final_marking': {k: v.value if hasattr(v, 'value') else v for k, v in final_marking.items()},
            'targets': targets,
        })

    target_rows = target_sets_as_rows(compute_target_sets(gm, targets))

    return sort_summary(summary), detailed, target_rows


def _summary_rows(summary: Any) -> List[dict]:
    if isinstance(summary, list):
        return [r for r in summary if isinstance(r, dict)]
    if isinstance(summary, dict):
        return []
    to_dict = getattr(summary, 'to_dict', None)
    if callable(to_dict):
        try:
            rows = to_dict(orient='records')
            return [r for r in rows if isinstance(r, dict)]
        except Exception:
            return []
    return []


def _as_str(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip()


def _normalize_traditional_class(row: dict) -> str:
    raw = _class_key(row.get('traditional_class', ''))
    if raw in {'optimal', 'non-optimal'}:
        return raw

    cost = row.get('alignment_cost', row.get('cost'))
    if cost is not None:
        try:
            return 'optimal' if float(cost) == 0.0 else 'non-optimal'
        except Exception:
            pass

    fitness = row.get('fitness')
    if fitness is not None:
        try:
            return 'optimal' if float(fitness) == 1.0 else 'non-optimal'
        except Exception:
            pass

    return 'non-optimal'


def _normalize_goal_class(row: dict) -> str:
    value = row.get('goal_class', row.get('compliance_class', row.get('classification', '')))
    key = _class_key(value)
    if key == 'strogly-compliant':
        key = 'strongly-compliant'
    mapping = {
        'strongly-compliant': 'strongly fulfilled',
        'weakly-compliant': 'weakly fulfilled',
        'non-compliant': 'non-fulfilled',
        'strongly-fulfilled': 'strongly fulfilled',
        'weakly-fulfilled': 'weakly fulfilled',
        'non-fulfilled': 'non-fulfilled',
    }
    return mapping.get(key, 'non-fulfilled')


def _trace_text(row: dict) -> str:
    if row.get('trace') is not None:
        return _as_str(row.get('trace'))
    if row.get('trace_text') is not None:
        return _as_str(row.get('trace_text'))
    if row.get('variant') is not None:
        return _as_str(row.get('variant'))
    return ''


def _split_activities(trace_text: str) -> List[str]:
    txt = _as_str(trace_text)
    if not txt:
        return []
    txt = txt.replace('<', '').replace('>', '').strip()
    if ' | ' in txt:
        return [x.strip() for x in txt.split(' | ') if x.strip()]
    if ',' in txt:
        return [x.strip() for x in txt.split(',') if x.strip()]
    if ';' in txt:
        return [x.strip() for x in txt.split(';') if x.strip()]
    return [x.strip() for x in txt.split() if x.strip()]


def _pct(part: int, total: int) -> float:
    return round((100.0 * part / total), 2) if total else 0.0


def _variant_frequency(rows: List[dict]) -> List[dict]:
    counter = Counter()
    for row in rows:
        counter[_trace_text(row)] += 1
    total = len(rows)
    out = []
    for variant, freq in counter.items():
        out.append({
            'variant': variant,
            'frequency': freq,
            'pct_within_case': _pct(freq, total),
        })
    return sorted(out, key=lambda x: (-x['frequency'], x['variant']))


def _pair_stats(rows: List[dict]) -> List[dict]:
    counter = Counter()
    for row in rows:
        acts = sorted(set(_split_activities(_trace_text(row))))
        for pair in combinations(acts, 2):
            counter[pair] += 1
    total = len(rows)
    out = []
    for pair, freq in counter.items():
        out.append({
            'activity_1': pair[0],
            'activity_2': pair[1],
            'trace_count': freq,
            'pct_within_case': _pct(freq, total),
        })
    return sorted(out, key=lambda x: (-x['trace_count'], x['activity_1'], x['activity_2']))


def _top_variant_sentence(variants: List[dict], label: str) -> str:
    if not variants:
        return f'No recurrent variants were observed for {label}.'
    top = variants[0]
    return (
        f"The most frequent variant in this category appears {int(top['frequency'])} times "
        f"({top['pct_within_case']}\\%) within the category."
    )


def _top_pair_sentence(pairs: List[dict], label: str) -> str:
    if not pairs:
        return f'No dominant activity pair was observed for {label}.'
    top = pairs[0]
    return (
        f"A recurrent activity pair is \\textit{{{top['activity_1']}}} and "
        f"\\textit{{{top['activity_2']}}}, appearing in {int(top['trace_count'])} traces "
        f"({top['pct_within_case']}\\%) of this category."
    )


def create_report(summary: Any) -> str:
    rows = _summary_rows(summary)
    normalized = []
    for row in rows:
        normalized.append({
            **row,
            'traditional_class': _normalize_traditional_class(row),
            'goal_class': _normalize_goal_class(row),
            'trace_text': _trace_text(row),
            'variant': _trace_text(row),
        })

    optimal_rows = [r for r in normalized if r['traditional_class'] == 'optimal']
    nonoptimal_rows = [r for r in normalized if r['traditional_class'] == 'non-optimal']

    opt_strong = sum(1 for r in optimal_rows if r['goal_class'] == 'strongly fulfilled')
    opt_weak = sum(1 for r in optimal_rows if r['goal_class'] == 'weakly fulfilled')
    opt_non = sum(1 for r in optimal_rows if r['goal_class'] == 'non-fulfilled')

    nonopt_strong = sum(1 for r in nonoptimal_rows if r['goal_class'] == 'strongly fulfilled')
    nonopt_weak = sum(1 for r in nonoptimal_rows if r['goal_class'] == 'weakly fulfilled')
    nonopt_non = sum(1 for r in nonoptimal_rows if r['goal_class'] == 'non-fulfilled')

    metrics = {
        'optimal_strong_pct': _pct(opt_strong, len(optimal_rows)),
        'optimal_weak_pct': _pct(opt_weak, len(optimal_rows)),
        'optimal_non_pct': _pct(opt_non, len(optimal_rows)),
        'nonoptimal_strong_pct': _pct(nonopt_strong, len(nonoptimal_rows)),
        'nonoptimal_weak_pct': _pct(nonopt_weak, len(nonoptimal_rows)),
        'nonoptimal_non_pct': _pct(nonopt_non, len(nonoptimal_rows)),
    }

    case_b = [
        r for r in normalized
        if r['traditional_class'] == 'non-optimal' and r['goal_class'] in {'strongly fulfilled', 'weakly fulfilled'}
    ]
    case_c = [
        r for r in normalized
        if r['traditional_class'] == 'optimal' and r['goal_class'] in {'weakly fulfilled', 'non-fulfilled'}
    ]
    case_d = [
        r for r in normalized
        if r['traditional_class'] == 'non-optimal' and r['goal_class'] == 'non-fulfilled'
    ]

    variants_b = _variant_frequency(case_b)
    variants_c = _variant_frequency(case_c)
    variants_d = _variant_frequency(case_d)

    pairs_b = _pair_stats(case_b)
    pairs_c = _pair_stats(case_c)
    pairs_d = _pair_stats(case_d)

    report_text = (
        f"\\paragraph{{Conformance vs Objectives Fulfillment}}\n"
        f"Among the traces with optimal alignments, {metrics['optimal_strong_pct']}\\% remain strongly fulfilled,\n"
        f"{metrics['optimal_weak_pct']}\\% are reclassified as weakly fulfilled, and\n"
        f"{metrics['optimal_non_pct']}\\% are reclassified as non-fulfilled.\n"
        f"This indicates that traditional alignment-based conformance may under-approximate problematic cases,\n"
        f"since behaviorally fitting traces may still fail to satisfy selected targets.\n\n"
        f"\\paragraph{{Tolerable Deviations: Non-compliant with the process model, objectives satisfied}}\n"
        f"Among the traces with non-optimal alignments, {metrics['nonoptimal_strong_pct']}\\% are still classified as strongly fulfilled and\n"
        f"{metrics['nonoptimal_weak_pct']}\\% as weakly fulfilled.\n"
        f"This shows that traditional conformance checking may over-approximate problematic behavior, since some deviations do not compromise the selected concerns.\n"
        f"{_top_variant_sentence(variants_b, 'tolerable deviations')}\n"
        f"{_top_pair_sentence(pairs_b, 'tolerable deviations')}\n\n"
        f"\\paragraph{{Apparently Acceptable Cases: Compliant with the process model, objectives not satisfied}}\n"
        f"Among the traces with optimal alignments, {metrics['optimal_strong_pct']}\\% remain strongly fulfilled,\n"
        f"{metrics['optimal_weak_pct']}\\% are reclassified as weakly fulfilled, and\n"
        f"{metrics['optimal_non_pct']}\\% are reclassified as non-fulfilled.\n"
        f"These results reveal traces that are acceptable from the control-flow perspective but unsatisfactory with respect to the selected targets.\n"
        f"{_top_variant_sentence(variants_c, 'apparently acceptable cases')}\n"
        f"{_top_pair_sentence(pairs_c, 'apparently acceptable cases')}\n\n"
        f"\\paragraph{{Critical Deviations: Non-compliant with the process model, objectives not satisfied}}\n"
        f"Among the traces with non-optimal alignments, {metrics['nonoptimal_non_pct']}\\% are classified as non-fulfilled.\n"
        f"These traces are problematic from both perspectives because they combine behavioral deviation with failure to satisfy the selected targets.\n"
        f"{_top_variant_sentence(variants_d, 'critical deviations')}\n"
        f"{_top_pair_sentence(pairs_d, 'critical deviations')}"
    )

    return report_text
