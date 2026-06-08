import pandas as pd
from IPython.display import HTML, Markdown, display

from Semantics.goccva.pipeline import ABSENCE
from Ui.goccva_helpers_ui import (
    CLASS_COLORS,
    FULFILMENT_COLORS,
    _case_from_analysis,
    _goal_class_to_fulfilment,
    _target_order_from_contribution,
    _target_rows_from_detailed_trace,
    build_target_computation_func,
    cell_style,
    classify_case,
    get_model_row,
    get_target_rows,
    render_activity_legend,
    render_label_legend,
    trace_to_abbrev,
)


def show_goal_oriented_alignment(summary, detailed, trace_id):
    trace_item = next((item for item in detailed if item.get("trace_id") == trace_id), None)

    if trace_item is None:
        print(f"trace_id {trace_id} was not found in detailed results")
        return

    summary_df = pd.DataFrame(summary)
    summary_trace_df = summary_df[summary_df["trace_id"] == trace_id]
    display(summary_trace_df)

    targets = trace_item.get("targets", [])
    for target in targets:
        alignment_rows = []
        for step_index, step in enumerate(trace_item.get("goal_oriented_alignment", []), start=1):
            move = step.get("move", ())
            mapped_tasks = ", ".join(step.get("mapped_tasks", []))
            target_theta = next((theta for theta in step.get("theta", []) if theta.get("target") == target), None)
            if target_theta is None:
                continue
            alignment_rows.append({
                "step": step_index,
                "log move": move[0] if len(move) > 0 else None,
                "model move": move[1] if len(move) > 1 else None,
                "mapped tasks": mapped_tasks,
                "label": target_theta.get("label"),
                "status": target_theta.get("status"),
            })

        print(f"Target: {target}")
        alignment_df = pd.DataFrame(alignment_rows)
        display(alignment_df)


def _render_distribution_matrix_from_summary(summary):
        """Render a 2x3 distribution matrix showing case counts and percentages."""
        bucket_order = ["O+", "O~", "O-", "N+", "N~", "N-"]
        counts = {bucket: 0 for bucket in bucket_order}

        for row in summary:
                if not isinstance(row, dict):
                        continue
                traditional_class = row.get("traditional_class", "")
                goal_class = row.get("goal_class", "")
                
                # Determine row symbol (O = Optimal, N = Non-optimal)
                trad_value = str(traditional_class or "").strip().lower()
                row_symbol = "O" if trad_value == "optimal" else "N"
                
                # Determine column symbol (+, ~, -)
                goal_value = str(goal_class or "").strip().lower().replace("_", "-").replace(" ", "-")
                if goal_value in {"strongly-compliant", "strogly-compliant", "strongly-fulfilled", "strong-fulfilled"}:
                        col_symbol = "+"
                elif goal_value in {"weakly-compliant", "weakly-fulfilled", "weak-fulfilled"}:
                        col_symbol = "~"
                else:
                        col_symbol = "-"
                
                bucket = f"{row_symbol}{col_symbol}"
                counts[bucket] += 1

        total_cases = sum(counts.values())
        
        def pct(bucket):
                if total_cases == 0:
                        return "0.0%"
                return f"{(counts[bucket] / total_cases) * 100:.1f}%"

        def bucket_cell(bucket):
                percentage = float(pct(bucket).rstrip('%'))
                gradient_stop = 100 - percentage
                return f"""
                <div style="
                        border:2px solid #2a2a2a;
                        border-radius:12px;
                        min-height:96px;
                        padding:10px 12px;
                        background: linear-gradient(to bottom, #ffffff {gradient_stop}%, #d4edda {gradient_stop}%);
                        display:flex;
                        flex-direction:column;
                        justify-content:center;
                        align-items:center;
                        gap:6px;
                ">
                    <div style="font-size:32px; font-style:italic; font-weight:700; line-height:1;">{bucket}</div>
                    <div style="font-size:15px; font-weight:700;">{pct(bucket)}</div>
                    <div style="font-size:13px; color:#333;">n = {counts[bucket]}</div>
                </div>
                """

        html = """
        <div style="margin-top:60px; margin-bottom:38px;">
            <h3 style="margin-bottom:20px;">Case Distribution Matrix</h3>
            <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:15px; max-width:600px;">
        """
        
        for bucket in bucket_order:
                html += bucket_cell(bucket)
        
        html += f"""
            </div>
            <p style="margin-top:20px; font-family:Arial, sans-serif; font-size:12px; color:#555;">
                <b>Total analysed traces:</b> {total_cases}
            </p>
        </div>
        """
        
        display(HTML(html))


def _render_goal_oriented_alignment(
    case,
    case_number,
    activity_abbreviations,
    target_computation_func=None,
    target_rows=None,
    extra_activity_marker="≫",
):
    trace = case["trace"]
    model_trace = case.get("model_trace")

    log_row = trace_to_abbrev(trace, activity_abbreviations)
    model_row = get_model_row(
        trace=trace,
        activity_abbreviations=activity_abbreviations,
        model_trace=model_trace,
        extra_activity_marker=extra_activity_marker,
    )

    alignment_class, fulfilment_class = classify_case(case)

    if target_rows is None:
        target_rows = get_target_rows(
            case=case,
            target_computation_func=target_computation_func,
        )

    n = max(len(log_row), len(model_row))

    # Filter out ABSENCE symbols for trace display
    log_row_for_display = [act for act in log_row if act != ABSENCE]

    html = f"""
    <div style="margin-top:30px; margin-bottom:38px;">
      <h3 style="margin-bottom:4px;">Case {case_number}: {case["requested_case"]}</h3>
      <p style="margin-top:0; font-family:Arial, sans-serif; font-size:13px;">
        <b>Trace:</b> {" → ".join(log_row_for_display)}
      </p>
      <p style="margin-top:0; font-family:Arial, sans-serif; font-size:13px;">
        <b>Explanation:</b> {case["why"]}
      </p>

      <div style="display:flex; align-items:flex-start; gap:36px;">

        <table style="border-collapse:collapse; font-family:Arial, sans-serif; font-size:13px;">
          <tr style="border-top:2px solid #333; border-bottom:1px solid #333;">
            <th style="padding:6px 8px;">Target</th>
            <th style="padding:6px 8px;">Value</th>
    """

    for i in range(1, n + 1):
        html += f'<th style="padding:6px 10px;">{i}</th>'

    html += """
          </tr>
          <tr>
            <td rowspan="2" style="padding:6px 8px; text-align:center; font-style:italic;">m<sub>i</sub></td>
            <td style="padding:6px 8px; font-weight:600;">log</td>
    """

    for i in range(n):
        value = log_row[i] if i < len(log_row) else extra_activity_marker
        html += f'<td style="padding:6px 10px; text-align:center;">{value}</td>'

    html += """
          </tr>
          <tr style="border-bottom:1px solid #333;">
            <td style="padding:6px 8px; font-weight:600;">model</td>
    """

    for i in range(n):
        value = model_row[i] if i < len(model_row) else extra_activity_marker
        html += f'<td style="padding:6px 10px; text-align:center;">{value}</td>'

    html += """
          </tr>
    """

    for _, target in target_rows.items():
        html += f"""
          <tr>
            <td rowspan="2" style="padding:6px 8px; text-align:center; font-style:italic;">{target["name"]}</td>
            <td style="padding:6px 8px; font-weight:600;">label</td>
        """

        labels = target["labels"]
        markings = target["markings"]

        for i in range(n):
            value = labels[i] if i < len(labels) else "ND"
            html += f'<td style="padding:6px 10px; {cell_style(value, "move")}">{value}</td>'

        html += """
          </tr>
          <tr style="border-bottom:1px solid #333;">
            <td style="padding:6px 8px; font-weight:600;">marking</td>
        """

        for i in range(n):
            value = markings[i] if i < len(markings) else "U"
            html += f'<td style="padding:6px 10px; {cell_style(value, "marking")}">{value}</td>'

        html += """
          </tr>
        """

    html += f"""
        </table>

        <div style="font-family:Arial, sans-serif; font-size:13px; min-width:190px; margin-top:42px;">
          <p style="font-weight:700; margin-bottom:18px;">Summary</p>

          <p style="margin-bottom:10px;">
            <b>Alignment class</b><br>
            <span style="color:{CLASS_COLORS.get(alignment_class, "#000")}; font-weight:700;">
              {alignment_class}
            </span>
          </p>

          <p>
            <b>Target fulfilment</b><br>
            <span style="color:{FULFILMENT_COLORS.get(fulfilment_class, "#000")}; font-weight:700;">
              {fulfilment_class}
            </span>
          </p>
        </div>

      </div>
    </div>
    """

    display(HTML(html))


def _render_goal_oriented_status_only(
        trace,
        trace_id,
        activity_abbreviations,
        target_rows,
        fulfilment_class,
        summary=None,
):
        trace_row = trace_to_abbrev(trace, activity_abbreviations)
        n = len(trace_row)

        html = f"""
        <div style="margin-top:30px; margin-bottom:38px;">
            <h3 style="margin-bottom:4px;">Trace {trace_id}</h3>
            <p style="margin-top:0; font-family:Arial, sans-serif; font-size:13px;">
                <b>Trace:</b> {" → ".join(trace_row)}
            </p>

            <div style="display:flex; align-items:flex-start; gap:36px;">

                <table style="border-collapse:collapse; font-family:Arial, sans-serif; font-size:13px;">
                    <tr style="border-top:2px solid #333; border-bottom:1px solid #333;">
                        <th style="padding:6px 8px;">Target</th>
                        <th style="padding:6px 8px;">Value</th>
        """

        for i in range(1, n + 1):
                html += f'<th style="padding:6px 10px;">{i}</th>'

        html += """
                    </tr>
                    <tr style="border-bottom:1px solid #333;">
                        <td style="padding:6px 8px; text-align:center; font-style:italic;">trace</td>
                        <td style="padding:6px 8px; font-weight:600;">activity</td>
        """

        for value in trace_row:
                html += f'<td style="padding:6px 10px; text-align:center;">{value}</td>'

        html += """
                    </tr>
        """

        for _, target in target_rows.items():
                labels = target["labels"]
                markings = target["markings"]

                html += f"""
                    <tr>
                        <td rowspan="2" style="padding:6px 8px; text-align:center; font-style:italic;">{target["name"]}</td>
                        <td style="padding:6px 8px; font-weight:600;">label</td>
                """

                for i in range(n):
                        value = labels[i] if i < len(labels) else "ND"
                        html += f'<td style="padding:6px 10px; {cell_style(value, "move")}">{value}</td>'

                html += """
                    </tr>
                    <tr style="border-bottom:1px solid #333;">
                        <td style="padding:6px 8px; font-weight:600;">status</td>
                """

                for i in range(n):
                        value = markings[i] if i < len(markings) else "U"
                        html += f'<td style="padding:6px 10px; {cell_style(value, "marking")}">{value}</td>'

                html += """
                    </tr>
                """

        html += f"""
                </table>

                <div style="font-family:Arial, sans-serif; font-size:13px; min-width:190px; margin-top:42px;">
                    <p style="font-weight:700; margin-bottom:18px;">Summary</p>

                    <p>
                        <b>Target fulfilment</b><br>
                        <span style="color:{FULFILMENT_COLORS.get(fulfilment_class, "#000")}; font-weight:700;">
                            {fulfilment_class}
                        </span>
                    </p>
                </div>

            </div>
        </div>
        """

        display(HTML(html))

        # Render distribution matrix if summary data is provided
        if summary is not None:
                _render_distribution_matrix_from_summary(summary)

# This is the old render function, which fakes the status of the goal model elements.
# This method should be removed in the final version of the code.
def render_all_goal_oriented_alignments(
    cases,
    activity_abbreviations,
    target_computation_func,
    title="Goal-oriented Process Alignment Examples",
    extra_activity_marker="≫",
):
    display(Markdown(f"# {title}"))

    display(Markdown(
        "The following cases illustrate combinations of alignment class "
        "and target-fulfilment class. Each table separates the process alignment row "
        "from the target-specific interpretation rows."
    ))

    render_activity_legend(activity_abbreviations)
    render_label_legend()

    for i, case in enumerate(cases, start=1):
        _render_goal_oriented_alignment(
            case=case,
            case_number=i,
            activity_abbreviations=activity_abbreviations,
            target_computation_func=target_computation_func,
            extra_activity_marker=extra_activity_marker,
        )

# Use this renderer for direct EventLog analysis. It does not require the
# hand-crafted "cases" structure and therefore cannot show "why" explanations.
def render_from_analysis(
    activity_abbreviations,
    summary,
    detailed,
    contribution_to_targets,
    title="Goal-oriented Process Alignment Examples",
    extra_activity_marker="≫",
):
    display(Markdown(f"# {title}"))

    display(Markdown(
        "The following cases illustrate combinations of alignment class "
        "and target-fulfilment class. Each table separates the process alignment row "
        "from the target-specific interpretation rows."
    ))

    render_activity_legend(activity_abbreviations)
    render_label_legend()

    ordered_targets = _target_order_from_contribution(contribution_to_targets)
    summary_by_trace_id = {
        row.get("trace_id"): row
        for row in summary
        if isinstance(row, dict)
    }

    for i, trace_item in enumerate(
        (row for row in detailed if isinstance(row, dict)), start=1
    ):
        trace_id = trace_item.get("trace_id")
        summary_row = summary_by_trace_id.get(trace_id)
        if summary_row is None:
            continue

        rendered_case = _case_from_analysis(
            case={},
            summary_row=summary_row,
            trace_item=trace_item,
            ordered_targets=ordered_targets,
        )

        _render_goal_oriented_alignment(
            case=rendered_case,
            case_number=i,
            activity_abbreviations=activity_abbreviations,
            target_rows=rendered_case["target_rows"],
            extra_activity_marker=extra_activity_marker,
        )

# This function shows the goal-oriented alignment tables only and does not
# need a process model as input. This can be used just to analyse the logs
# in case a process model is not available or the focus is only on goal fulfilment.
def render_no_pm(
    activity_abbreviations,
    summary,
    detailed,
    contribution_to_targets,
    title="Goal-oriented Status Evolution Examples",
):
    display(Markdown(f"# {title}"))

    display(Markdown(
        "The following traces show how target statuses evolve over time "
        "without using process-model alignments."
    ))

    render_activity_legend(activity_abbreviations)
    render_label_legend()

    ordered_targets = _target_order_from_contribution(contribution_to_targets)
    summary_by_trace_id = {
        row.get("trace_id"): row
        for row in summary
        if isinstance(row, dict)
    }

    for i, trace_item in enumerate(
        (row for row in detailed if isinstance(row, dict)), start=1
    ):
        trace_id = trace_item.get("trace_id")
        summary_row = summary_by_trace_id.get(trace_id)
        if summary_row is None:
            continue

        target_rows = _target_rows_from_detailed_trace(trace_item, ordered_targets)
        fulfilment_class = _goal_class_to_fulfilment(summary_row.get("goal_class"))

        _render_goal_oriented_status_only(
            trace=trace_item.get("trace", []),
            trace_id=i,
            activity_abbreviations=activity_abbreviations,
            target_rows=target_rows,
            fulfilment_class=fulfilment_class,
            summary=summary,
        )

# Use this renderer when hand-crafted "cases" are available. The cases provide
# the "why" explanations; labels and markings still come from the analysed
# EventLog. Use render_from_analysis for direct EventLog analysis without cases.
def render_all_goal_oriented_alignments_from_analysis(
    cases,
    activity_abbreviations,
    summary,
    detailed,
    contribution_to_targets,
    title="Goal-oriented Process Alignment Examples",
    extra_activity_marker="≫",
):
    display(Markdown(f"# {title}"))

    display(Markdown(
        "The following cases illustrate combinations of alignment class "
        "and target-fulfilment class. Each table separates the process alignment row "
        "from the target-specific interpretation rows."
    ))

    render_activity_legend(activity_abbreviations)
    render_label_legend()

    ordered_targets = _target_order_from_contribution(contribution_to_targets)
    summary_by_trace_id = {
        row.get("trace_id"): row
        for row in summary
        if isinstance(row, dict)
    }
    detailed_by_trace_id = {
        row.get("trace_id"): row
        for row in detailed
        if isinstance(row, dict)
    }

    for i, case in enumerate(cases, start=1):
        summary_row = summary_by_trace_id.get(i)
        trace_item = detailed_by_trace_id.get(i)
        if summary_row is None or trace_item is None:
            continue

        rendered_case = _case_from_analysis(
            case=case,
            summary_row=summary_row,
            trace_item=trace_item,
            ordered_targets=ordered_targets,
        )

        _render_goal_oriented_alignment(
            case=rendered_case,
            case_number=i,
            activity_abbreviations=activity_abbreviations,
            target_rows=rendered_case["target_rows"],
            extra_activity_marker=extra_activity_marker,
        )


def _traditional_class_to_matrix_row_symbol(traditional_class):
        value = str(traditional_class or "").strip().lower()
        if value == "optimal":
                return "O"
        return "N"


def _goal_class_to_matrix_column_symbol(goal_class):
        value = str(goal_class or "").strip().lower().replace("_", "-").replace(" ", "-")
        if value in {
                "strongly-compliant",
                "strogly-compliant",
                "strongly-fulfilled",
                "strong-fulfilled",
        }:
                return "+"
        if value in {
                "weakly-compliant",
                "weakly-fulfilled",
                "weak-fulfilled",
        }:
                return "~"
        return "-"


def _render_case_distribution_matrix_from_summary(summary, title, targets=None):
        bucket_order = ["O+", "O~", "O-", "N+", "N~", "N-"]
        counts = {bucket: 0 for bucket in bucket_order}

        for row in summary:
                if not isinstance(row, dict):
                        continue
                row_symbol = _traditional_class_to_matrix_row_symbol(row.get("traditional_class"))
                col_symbol = _goal_class_to_matrix_column_symbol(row.get("goal_class"))
                counts[f"{row_symbol}{col_symbol}"] += 1

        total_cases = sum(counts.values())

        row_totals = {
            "O": counts["O+"] + counts["O~"] + counts["O-"],
            "N": counts["N+"] + counts["N~"] + counts["N-"],
        }
        column_totals = {
            "+": counts["O+"] + counts["N+"],
            "~": counts["O~"] + counts["N~"],
            "-": counts["O-"] + counts["N-"],
        }

        def pct(bucket):
                if total_cases == 0:
                        return "0.0%"
                return f"{(counts[bucket] / total_cases) * 100:.1f}%"

        def pct_for_count(value):
            if total_cases == 0:
                return "0.0%"
            return f"{(value / total_cases) * 100:.1f}%"

        def total_text(value):
            return f"{pct_for_count(value)} (n = {value})"

        def bucket_cell(bucket):
                percentage = float(pct(bucket).rstrip('%'))
                gradient_stop = 100 - percentage
                return f"""
                <div style="
                        border:2px solid #2a2a2a;
                        border-radius:12px;
                        min-height:96px;
                        padding:10px 12px;
                        background: linear-gradient(to bottom, #ffffff {gradient_stop}%, #d4edda {gradient_stop}%);
                        display:flex;
                        flex-direction:column;
                        justify-content:center;
                        align-items:center;
                        gap:6px;
                ">
                    <div style="font-size:32px; font-style:italic; font-weight:700; line-height:1;">{bucket}</div>
                    <div style="font-size:15px; font-weight:700;">{pct(bucket)}</div>
                    <div style="font-size:13px; color:#333;">n = {counts[bucket]}</div>
                </div>
                """

        targets_html = ""
        if targets:
                targets_list = "<br>".join(f"• {t}" for t in targets)
                targets_html = f"""
            <p style="margin-top:16px; margin-bottom:0; font-size:13px; color:#333;">
                <b>Evaluated targets:</b><br>
                {targets_list}
            </p>
            """

        html = f"""
        <div style="font-family:Arial, sans-serif; margin:18px 0 12px 0; color:#111;">
            <h3 style="margin:0 0 14px 0; font-size:22px;">{title}</h3>

            <div style="display:grid; grid-template-columns: 140px 1fr; gap:12px; align-items:stretch;">
                <div style="display:flex; align-items:center; justify-content:center;">
                    <div style="writing-mode:vertical-rl; transform:rotate(180deg); font-size:28px; font-weight:600; text-align:center;">
                        Behavioral conformance
                    </div>
                </div>

                <div style="border:2px dashed #444; border-radius:12px; padding:14px;">
                    <div style="display:grid; grid-template-columns: 92px repeat(3, minmax(160px, 1fr)); gap:14px; align-items:center;">
                        <div></div>
                        <div></div>
                        <div></div>
                        <div></div>

                        <div style="text-align:center;">
                            <div style="font-size:17px; font-weight:700;">Optimal</div>
                            <div style="font-size:12px; color:#444; margin-top:3px;">{total_text(row_totals["O"])}</div>
                        </div>
                        {bucket_cell("O+")}
                        {bucket_cell("O~")}
                        {bucket_cell("O-")}

                        <div style="text-align:center;">
                            <div style="font-size:17px; font-weight:700;">Non-optimal</div>
                            <div style="font-size:12px; color:#444; margin-top:3px;">{total_text(row_totals["N"])}</div>
                        </div>
                        {bucket_cell("N+")}
                        {bucket_cell("N~")}
                        {bucket_cell("N-")}
                    </div>

                    <div style="margin-top:14px; display:grid; grid-template-columns: 92px repeat(3, minmax(160px, 1fr)); gap:14px; text-align:center; font-size:14px; font-weight:600;">
                        <div></div>
                        <div>
                            <div>Strong fulfilled</div>
                            <div style="font-size:12px; color:#444; margin-top:3px; font-weight:500;">{total_text(column_totals["+"])}</div>
                        </div>
                        <div>
                            <div>Weakly fulfilled</div>
                            <div style="font-size:12px; color:#444; margin-top:3px; font-weight:500;">{total_text(column_totals["~"])}</div>
                        </div>
                        <div>
                            <div>Non-fulfilled</div>
                            <div style="font-size:12px; color:#444; margin-top:3px; font-weight:500;">{total_text(column_totals["-"])}</div>
                        </div>
                    </div>

                </div>
            </div>

            {targets_html}

            <p style="margin:12px 0 0 0; font-size:13px; color:#333;">
                Total analysed traces: <b>{total_cases}</b>
            </p>
        </div>
        """

        display(HTML(html))
        return html, counts


def render_case_distribution_matrix(
    summary,
    title="Case Distribution Matrix",
    targets=None,
):
    html, counts = _render_case_distribution_matrix_from_summary(
        summary=summary,
        title=title,
        targets=targets,
    )

    return {
        "summary": summary,
        "counts": counts,
        "html": html,
    }


def render_case_distribution_matrix_from_analysis(
    summary,
    title="Case Distribution Matrix",
    targets=None,
):
    return render_case_distribution_matrix(
        summary=summary,
        title=title,
        targets=targets,
    )
