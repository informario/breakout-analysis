from typing import List, Optional

try:
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except Exception:
    _HAS_PLOTLY = False


def plot_linecard_heatmaps(
    step_history: List[List[List[str]]],
    linecard_order: Optional[List[str]] = None,
    max_attempts: Optional[int] = None,
    title_prefix: str = "Step",
    best_attempt_indices: Optional[List[int]] = None,
):
    """Plot presence heatmaps per step across attempts.

    step_history: list[attempt][step][linecard_code]
    Each heatmap shows attempts (rows) vs linecards (columns).
    """
    if not _HAS_PLOTLY:
        raise RuntimeError("plotly is required for heatmaps")
    if not step_history:
        return

    attempts = step_history
    if max_attempts is not None and max_attempts > 0:
        attempts = attempts[:max_attempts]

    step_count = max(len(attempt) for attempt in attempts)

    if linecard_order is None:
        codes = set()
        for attempt in attempts:
            for step in attempt:
                codes.update(step)
        linecard_order = sorted(codes)

    if not linecard_order:
        return

    combined = []
    for attempt in attempts:
        row = []
        for step_idx in range(step_count):
            step_codes = set(attempt[step_idx]) if step_idx < len(attempt) else set()
            row.extend([1 if code in step_codes else 0 for code in linecard_order])
        combined.append(row)

    if not combined:
        return

    step_labels = [f"{title_prefix} {i}" for i in range(step_count)]
    x_labels = []
    for step_label in step_labels:
        for code in linecard_order:
            x_labels.append(f"{step_label}:{code}")

    fig = go.Figure(
        data=go.Heatmap(
            z=combined,
            x=x_labels,
            y=list(range(len(combined))),
            colorscale="Viridis",
            colorbar=dict(title="Presence"),
        )
    )

    fig.update_layout(
        title=f"{title_prefix} Heatmap",
        xaxis_title=None,
        yaxis_title=None,
        xaxis=dict(tickangle=90, showticklabels=False),
        yaxis=dict(autorange="reversed"),
        height=max(300, int(len(combined) * 12)),
        width=max(600, int(len(x_labels) * 10)),
        margin=dict(l=60, r=20, t=50, b=120),
    )

    shapes = []
    for step_idx in range(1, step_count):
        x_pos = step_idx * len(linecard_order) - 0.5
        shapes.append(
            dict(
                type="line",
                x0=x_pos,
                x1=x_pos,
                y0=-0.5,
                y1=len(combined) - 0.5,
                line=dict(color="white", width=1),
            )
        )

    if best_attempt_indices:
        for attempt_idx in best_attempt_indices:
            if 0 <= attempt_idx < len(combined):
                shapes.append(
                    dict(
                        type="line",
                        x0=-0.5,
                        x1=len(x_labels) - 0.5,
                        y0=attempt_idx,
                        y1=attempt_idx,
                        line=dict(color="red", width=1),
                    )
                )

    if shapes:
        fig.update_layout(shapes=shapes)

    fig.show()
