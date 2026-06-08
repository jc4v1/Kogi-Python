#This is a test
from __future__ import annotations

import argparse
import csv
import math
import statistics
import time
from pathlib import Path
from typing import Iterable, Sequence

from Semantics.enums import ElementStatus
from Semantics.parsers.istar_processor import read_istar_model
from Semantics.goccva.label_assignment import ABSENCE
from Semantics.goccva.target_sets import compute_target_sets


DEFAULT_LENGTHS = [5, 10, 25, 50, 100, 200, 500, 1000]


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def parse_lengths(value: str) -> list[int]:
    lengths = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not lengths or any(length <= 0 for length in lengths):
        raise argparse.ArgumentTypeError("lengths must be positive integers")
    return lengths


def model_size_parameters(goal_model, targets: list[str]) -> dict[str, int]:
    return {
        "K_targets": len(targets),
        "N_intentional_elements": len(goal_model.elements()),
        "E_links_plus_dependencies": len(goal_model.links) + len(goal_model.dependencies),
        "L_leaf_tasks": len(goal_model.leaves()),
        "Q_qualities": len(goal_model.qualities),
        "G_goals": len(goal_model.goals),
        "T_tasks": len(goal_model.tasks),
    }


def default_targets(goal_model) -> list[str]:
    if goal_model.qualities:
        return sorted(goal_model.qualities)
    return sorted(goal_model.goals)[:1] or sorted(goal_model.tasks)[:1]


def default_activity_mapping(goal_model) -> dict[str, set[str]]:
    leaves = sorted(goal_model.leaves())
    return {leaf: {leaf} for leaf in leaves}


def synthetic_alignment(events: list[str], length: int, include_model_moves: bool = False) -> list[tuple[str, ...]]:
    if not events:
        raise ValueError("Cannot build a synthetic alignment: the goal model has no leaf-task events.")
    moves: list[tuple[str, ...]] = []
    for index in range(length):
        event = events[index % len(events)]
        if include_model_moves and index % 11 == 10:
            moves.append((ABSENCE, event))
        else:
            moves.append((event,))
    return moves


def move_activity(move: Sequence[str], include_model_fallback: bool = False) -> str:
    if not move:
        return ABSENCE
    log_activity = move[0] if len(move) > 0 and move[0] is not None else ABSENCE
    if log_activity != ABSENCE:
        return log_activity
    if include_model_fallback and len(move) > 1 and move[1] is not None:
        return move[1]
    return ABSENCE


def map_move(activity_mapping: dict[str, set[str]], move: Sequence[str]) -> set[str]:
    activity = move_activity(move)
    if activity == ABSENCE:
        return set()
    return activity_mapping.get(activity, set())


def map_move_for_label(activity_mapping: dict[str, set[str]], move: Sequence[str]) -> set[str]:
    activity = move_activity(move, include_model_fallback=True)
    if activity == ABSENCE:
        return set()
    return activity_mapping.get(activity, set())


def label_move(
    target: str,
    move: Sequence[str],
    activity_mapping: dict[str, set[str]],
    target_sets,
) -> str:
    mapped_elements = map_move_for_label(activity_mapping, move)
    if not mapped_elements:
        return "ND"
    make_set, break_set, nr_set = target_sets[target]
    if mapped_elements & make_set:
        return "M"
    if mapped_elements & break_set:
        return "B"
    if mapped_elements & nr_set:
        return "NR"
    return "ND"


def fulfillment_class(targets: list[str], status_history: dict[str, list[ElementStatus]]) -> str:
    weak = all(status_history[target] and status_history[target][-1] == ElementStatus.SATISFIED for target in targets)
    stable = True
    for target in targets:
        seen_satisfied = False
        for status in status_history[target]:
            if status == ElementStatus.SATISFIED:
                seen_satisfied = True
            elif seen_satisfied and status != ElementStatus.SATISFIED:
                stable = False
                break
        if not stable:
            break
    if not weak:
        return "Non-fulfilled"
    return "Strongly fulfilled" if stable else "Weakly fulfilled"


def compute_goal_oriented_alignment_postprocessing(
    goal_model,
    alignment: list[Sequence[str]],
    activity_mapping: dict[str, set[str]],
    targets: list[str],
    initial_marking: dict[str, ElementStatus] | None = None,
) -> tuple[list[dict], dict[str, ElementStatus], str]:
    goal_model.reset()
    if initial_marking:
        goal_model.set_markings(initial_marking)

    target_sets = compute_target_sets(goal_model, targets)
    go_alignment = []
    status_history = {target: [] for target in targets}

    for move in alignment:
        mapped = map_move(activity_mapping, move)
        if mapped:
            goal_model.fire_elements(mapped)
        marking = goal_model.get_markings()

        theta = []
        for target in targets:
            theta.append(
                {
                    "target": target,
                    "label": label_move(target, move, activity_mapping, target_sets),
                    "status": marking[target].value if hasattr(marking[target], "value") else marking[target],
                }
            )
            status_history[target].append(marking[target])
        go_alignment.append({"move": move, "mapped_tasks": sorted(mapped), "theta": theta})

    return go_alignment, marking, fulfillment_class(targets, status_history)


def time_call(fn, repeats: int) -> dict[str, float]:
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        timings.append(time.perf_counter() - start)
    return {
        "min_s": min(timings),
        "median_s": statistics.median(timings),
        "mean_s": statistics.mean(timings),
        "max_s": max(timings),
    }


def linear_fit(xs: list[float], ys: list[float]) -> dict[str, float]:
    if len(xs) < 2:
        return {"slope_s_per_move": math.nan, "intercept_s": math.nan, "r2": math.nan}

    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys)
    sxx = sum((x - x_mean) ** 2 for x in xs)
    if sxx == 0:
        return {"slope_s_per_move": math.nan, "intercept_s": math.nan, "r2": math.nan}
    sxy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    predicted = [intercept + slope * x for x in xs]
    ss_res = sum((y - y_hat) ** 2 for y, y_hat in zip(ys, predicted))
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    r2 = 1.0 if ss_tot == 0 else 1.0 - (ss_res / ss_tot)
    return {"slope_s_per_move": slope, "intercept_s": intercept, "r2": r2}


def write_csv(path: Path, rows: Iterable[dict]) -> None:
    rows = list(rows)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_report(
    path: Path,
    model_path: Path,
    targets: list[str],
    params: dict[str, int],
    target_set_timing: dict[str, float],
    benchmark_rows: list[dict],
    fit: dict[str, float],
) -> None:
    lines = [
        "# GoCCvA Computational Complexity Analysis",
        "",
        f"Goal model: `{model_path}`",
        "",
        "## Theoretical Bound",
        "",
        "For one alignment of length `n`, with cached structural information, the post-processing layer is:",
        "",
        "`O(K * L + n * (K + N + E))`",
        "",
        "where `K` is the number of selected targets, `L` is the number of leaf tasks, "
        "`N` is the number of intentional elements, and `E` is the number of refinement, contribution, and dependency links.",
        "",
        "For a fixed goal model and fixed target set, `K`, `L`, `N`, and `E` are constants, so the runtime is linear in `n`.",
        "",
        "## Model Parameters",
        "",
        "| Parameter | Value |",
        "|---|---:|",
    ]
    for key, value in params.items():
        lines.append(f"| `{key}` | {value} |")

    lines.extend([
        "",
        "Targets:",
        "",
    ])
    lines.extend(f"- `{target}`" for target in targets)
    lines.extend([
        "",
        "## Target-Set Computation Timing",
        "",
        "| Metric | Seconds |",
        "|---|---:|",
    ])
    for key, value in target_set_timing.items():
        lines.append(f"| `{key}` | {value:.8f} |")

    lines.extend([
        "",
        "## Alignment-Length Scaling",
        "",
        "| n moves | median seconds | median ms / move |",
        "|---:|---:|---:|",
    ])
    for row in benchmark_rows:
        lines.append(
            f"| {row['n_moves']} | {row['median_s']:.8f} | {row['median_ms_per_move']:.6f} |"
        )

    lines.extend([
        "",
        "## Linear Fit",
        "",
        f"- Slope: `{fit['slope_s_per_move']:.10f}` seconds per move",
        f"- Intercept: `{fit['intercept_s']:.8f}` seconds",
        f"- R^2: `{fit['r2']:.6f}`",
        "",
        "A high R^2 close to 1 supports the expected linear scaling in the alignment length for this fixed model and target set.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze GoCCvA post-processing complexity.")
    parser.add_argument(
        "--goal-model",
        default="content/test/test0e_fail.txt",
        help="Path to an iStar goal model JSON/TXT file.",
    )
    parser.add_argument(
        "--qualified",
        default="true",
        help="Whether to read actor-qualified element names.",
    )
    parser.add_argument(
        "--targets",
        default="",
        help="Comma-separated target names. Defaults to all qualities.",
    )
    parser.add_argument(
        "--lengths",
        type=parse_lengths,
        default=DEFAULT_LENGTHS,
        help="Comma-separated synthetic alignment lengths.",
    )
    parser.add_argument("--repeats", type=int, default=5, help="Benchmark repeats per length.")
    parser.add_argument(
        "--include-model-moves",
        action="store_true",
        help="Include periodic model moves in the synthetic alignments.",
    )
    parser.add_argument("--out-dir", default="complexity_results", help="Output directory.")
    args = parser.parse_args()

    if args.repeats <= 0:
        raise ValueError("--repeats must be positive")

    model_path = Path(args.goal_model)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    goal_model = read_istar_model(str(model_path), qualified=parse_bool(args.qualified))
    targets = [part.strip() for part in args.targets.split(",") if part.strip()]
    if not targets:
        targets = default_targets(goal_model)
    missing_targets = [target for target in targets if target not in goal_model.elements()]
    if missing_targets:
        raise ValueError(f"Targets not found in goal model: {missing_targets}")

    activity_mapping = default_activity_mapping(goal_model)
    activity_mapping = goal_model.canonicalize_activity_mapping(activity_mapping)
    events = sorted(activity_mapping)

    params = model_size_parameters(goal_model, targets)
    target_set_timing = time_call(lambda: compute_target_sets(goal_model, targets), args.repeats)

    benchmark_rows = []
    for length in args.lengths:
        alignment = synthetic_alignment(events, length, include_model_moves=args.include_model_moves)

        def run_once() -> None:
            compute_goal_oriented_alignment_postprocessing(goal_model, alignment, activity_mapping, targets)

        timing = time_call(run_once, args.repeats)
        row = {
            "n_moves": length,
            **timing,
            "median_ms_per_move": (timing["median_s"] / length) * 1000.0,
            "predicted_bound_units": params["K_targets"] * params["L_leaf_tasks"]
            + length * (params["K_targets"] + params["N_intentional_elements"] + params["E_links_plus_dependencies"]),
        }
        benchmark_rows.append(row)

    fit = linear_fit(
        [float(row["n_moves"]) for row in benchmark_rows],
        [float(row["median_s"]) for row in benchmark_rows],
    )

    write_csv(out_dir / "goccva_complexity_benchmark.csv", benchmark_rows)
    write_csv(out_dir / "goccva_complexity_parameters.csv", [params])
    write_markdown_report(
        out_dir / "goccva_complexity_report.md",
        model_path=model_path,
        targets=targets,
        params=params,
        target_set_timing=target_set_timing,
        benchmark_rows=benchmark_rows,
        fit=fit,
    )

    print("Wrote:")
    print(f"- {out_dir / 'goccva_complexity_parameters.csv'}")
    print(f"- {out_dir / 'goccva_complexity_benchmark.csv'}")
    print(f"- {out_dir / 'goccva_complexity_report.md'}")
    print()
    print("Linear fit:")
    print(f"  slope_s_per_move = {fit['slope_s_per_move']:.10f}")
    print(f"  intercept_s      = {fit['intercept_s']:.8f}")
    print(f"  r2               = {fit['r2']:.6f}")


if __name__ == "__main__":
    main()
