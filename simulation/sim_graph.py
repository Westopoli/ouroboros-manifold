"""
sim_graph.py — Shared graphing for simulation tuning.

Produces one PNG per scenario with all factions overlaid.
Consistent colors per field, consistent line styles per faction.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

# ── Visual constants ─────────────────────────────────────────────────────────

FIELD_COLORS = {
    "military":   "#c0392b",  # red
    "economy":    "#27ae60",  # green
    "tension":    "#e67e22",  # orange
    "population": "#2980b9",  # blue
    "tech_level": "#8e44ad",  # purple
}

FIELD_LABELS = {
    "military":   "Military",
    "economy":    "Economy",
    "tension":    "Tension",
    "population": "Population",
    "tech_level": "Tech Level",
}

# Up to 6 factions; each gets a distinct line style
FACTION_STYLES = [
    {"ls": "-",   "lw": 1.8},   # solid
    {"ls": "--",  "lw": 1.8},   # dashed
    {"ls": "-.",  "lw": 1.6},   # dashdot
    {"ls": ":",   "lw": 2.0},   # dotted
    {"ls": (0, (5, 1)),     "lw": 1.6},   # tight dash
    {"ls": (0, (3, 1, 1, 1)), "lw": 1.6}, # dash-dot-dot
]

BG_OUTER = "#1a1a2e"
BG_INNER = "#16213e"


def make_scenario_graph(scenario_name: str,
                        description: str,
                        ticks_list: list,
                        faction_data: dict,
                        fields: list,
                        output_path: str,
                        region_counts: dict | None = None,
                        extra_info: str = "",
                        event_log: list | None = None):
    """
    Produce one PNG showing all factions overlaid.

    faction_data: {
        "faction_label": {
            "display_name": str,
            "fields": {
                "military": [values...],
                "economy": [values...],
                ...
            }
        }
    }
    fields: which fields to plot, e.g. ["military", "economy", "tension", "population"]
    region_counts: {faction_label: int} — shown in legend
    """
    n_factions = len(faction_data)
    # Dynamic figure height: taller for more factions so legend doesn't overlap
    fig_h = 7 + max(0, n_factions - 2) * 0.5
    fig, ax = plt.subplots(figsize=(16, fig_h))
    fig.patch.set_facecolor(BG_OUTER)
    ax.set_facecolor(BG_INNER)

    max_tick = max(ticks_list)

    # Plot each faction × field combination
    for fac_idx, (fac_label, fac_info) in enumerate(faction_data.items()):
        style = FACTION_STYLES[fac_idx % len(FACTION_STYLES)]
        display = fac_info["display_name"]
        n_regions = region_counts.get(fac_label, "?") if region_counts else ""
        suffix = f" [{n_regions}r]" if n_regions != "" else ""

        for field in fields:
            values = fac_info["fields"].get(field, [])
            if not values:
                continue

            label = f"{display}{suffix} — {FIELD_LABELS[field]}" if fac_idx == 0 or n_factions <= 2 else None
            # For multi-faction, build label only for first field per faction + first faction per field
            # Actually, let's use a smarter legend approach
            label = None  # we'll build custom legend

            ax.plot(ticks_list[:len(values)], values,
                    color=FIELD_COLORS[field],
                    linewidth=style["lw"],
                    linestyle=style["ls"],
                    alpha=0.85)

            # End-value annotation
            if len(values) > 0:
                y_offset = fac_idx * 10 - (n_factions - 1) * 5  # spread annotations vertically
                ax.annotate(
                    f"{values[-1]:.1f}",
                    xy=(ticks_list[len(values)-1], values[-1]),
                    xytext=(8, y_offset // max(n_factions, 1)),
                    textcoords="offset points",
                    color=FIELD_COLORS[field],
                    fontsize=7 if n_factions > 2 else 8,
                    fontweight="bold",
                    va="center",
                    alpha=0.7 + 0.3 * (1 if fac_idx == 0 else 0),
                )

    # ── Custom legend: field colors + faction line styles ────────────────────
    from matplotlib.lines import Line2D

    legend_elements = []

    # Field color entries
    for field in fields:
        legend_elements.append(
            Line2D([0], [0], color=FIELD_COLORS[field], linewidth=2.0,
                   label=FIELD_LABELS[field])
        )

    # Separator
    legend_elements.append(Line2D([0], [0], color="none", label=""))

    # Faction line style entries
    for fac_idx, (fac_label, fac_info) in enumerate(faction_data.items()):
        style = FACTION_STYLES[fac_idx % len(FACTION_STYLES)]
        display = fac_info["display_name"]
        n_regions = region_counts.get(fac_label, "") if region_counts else ""
        suffix = f" [{n_regions}r]" if n_regions != "" else ""
        legend_elements.append(
            Line2D([0], [0], color="#c0c0c0", linewidth=style["lw"],
                   linestyle=style["ls"], label=f"{display}{suffix}")
        )

    ax.legend(handles=legend_elements, loc="upper right", fontsize=9,
              facecolor=BG_OUTER, edgecolor="#404060", labelcolor="#c0c0c0",
              ncol=1)

    # ── Axes formatting ──────────────────────────────────────────────────────
    ax.set_xlim(0, max_tick + 20)
    ax.set_ylim(0, 105)
    ax.set_xlabel("Tick", color="#a0a0a0", fontsize=12)
    ax.set_ylabel("Value (0–100)", color="#a0a0a0", fontsize=12)

    title = f"{scenario_name}"
    if description:
        title += f"\n{description}"
    ax.set_title(title, color="#e0e0e0", fontsize=13, fontweight="bold", pad=15)

    ax.tick_params(colors="#707070")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#404060")
    ax.spines["bottom"].set_color("#404060")
    ax.grid(True, alpha=0.15, color="#ffffff")

    # Extra info in bottom-left
    if extra_info:
        ax.text(0.02, 0.02, extra_info, transform=ax.transAxes,
                fontsize=8, color="#808080", va="bottom",
                fontfamily="monospace")

    # Event markers
    if event_log:
        _draw_event_markers(ax, event_log)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


def _format_ax(ax):
    """Apply shared axis styling."""
    ax.tick_params(colors="#707070")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#404060")
    ax.spines["bottom"].set_color("#404060")
    ax.grid(True, alpha=0.15, color="#ffffff")


def _draw_event_markers(ax, event_log: list):
    """Draw vertical lines + triangle markers at event ticks.
    Groups events on the same tick to avoid stacking labels."""
    if not event_log:
        return

    # Group by tick
    by_tick = {}
    for evt in event_log:
        t = evt["tick"]
        by_tick.setdefault(t, []).append(evt)

    for t, events in by_tick.items():
        # Thin vertical line spanning the plot
        ax.axvline(x=t, color="#ffffff", alpha=0.18, linewidth=0.8, zorder=1)

        # Triangle marker at the top
        ax.plot(t, 102, marker="v", color="#ff6b6b", markersize=6, alpha=0.8,
                zorder=5, clip_on=False)

        # Label: event name(s), stacked if multiple
        names = list(dict.fromkeys(e["name"] for e in events))  # dedupe, preserve order
        label = "\n".join(names[:3])  # cap at 3 lines
        if len(names) > 3:
            label += f"\n+{len(names)-3} more"
        ax.annotate(label,
                    xy=(t, 103), xytext=(3, 6), textcoords="offset points",
                    fontsize=6, color="#ff6b6b", alpha=0.7, va="bottom",
                    rotation=45, ha="left")


def make_sidebyside_graph(scenario_name: str,
                          variant_results: list,
                          fields: list,
                          output_path: str):
    """
    Side-by-side panels — one panel per variant, same y-axis scale.

    variant_results: [
        {
            "label": "Normal economy",
            "ticks_list": [...],
            "faction_data": { fid: { "display_name": ..., "fields": {...} } },
            "region_counts": { fid: int },
            "extra_info": str,
        },
        ...
    ]
    """
    from matplotlib.lines import Line2D

    n = len(variant_results)
    if n <= 2:
        nrows, ncols = 1, n
    else:
        nrows = 2
        ncols = (n + 1) // 2
    fig, axes_grid = plt.subplots(nrows, ncols, figsize=(10 * ncols, 8 * nrows), sharey=True)
    fig.patch.set_facecolor(BG_OUTER)
    if n == 1:
        axes = [axes_grid]
    else:
        axes = axes_grid.flatten().tolist()
    # Hide unused panels if n is odd and > 2
    for i in range(n, len(axes)):
        axes[i].set_visible(False)

    for panel_idx, variant in enumerate(variant_results):
        ax = axes[panel_idx]
        ax.set_facecolor(BG_INNER)

        ticks_list = variant["ticks_list"]
        faction_data = variant["faction_data"]
        region_counts = variant.get("region_counts", {})
        max_tick = max(ticks_list)

        for fac_idx, (fac_label, fac_info) in enumerate(faction_data.items()):
            style = FACTION_STYLES[fac_idx % len(FACTION_STYLES)]

            for field in fields:
                values = fac_info["fields"].get(field, [])
                if not values:
                    continue
                ax.plot(ticks_list[:len(values)], values,
                        color=FIELD_COLORS[field],
                        linewidth=style["lw"],
                        linestyle=style["ls"],
                        alpha=0.85)

                # End-value annotation
                n_factions = len(faction_data)
                y_off = fac_idx * 8 - (n_factions - 1) * 4
                ax.annotate(
                    f"{values[-1]:.1f}",
                    xy=(ticks_list[len(values)-1], values[-1]),
                    xytext=(6, y_off // max(n_factions, 1)),
                    textcoords="offset points",
                    color=FIELD_COLORS[field],
                    fontsize=8, fontweight="bold", va="center",
                )

        ax.set_xlim(0, max_tick + 15)
        ax.set_ylim(0, 105)
        ax.set_xlabel("Tick", color="#a0a0a0", fontsize=11)
        if panel_idx == 0:
            ax.set_ylabel("Value (0–100)", color="#a0a0a0", fontsize=11)
        ax.set_title(variant["label"], color="#e0e0e0", fontsize=12, fontweight="bold")
        _format_ax(ax)

        # Extra info in bottom-left
        extra = variant.get("extra_info", "")
        if extra:
            ax.text(0.02, 0.02, extra, transform=ax.transAxes,
                    fontsize=7, color="#808080", va="bottom", fontfamily="monospace")

        # Event markers
        evt_log = variant.get("event_log", [])
        if evt_log:
            _draw_event_markers(ax, evt_log)

    # ── Shared legend on the right side ──────────────────────────────────────
    legend_elements = []
    for field in fields:
        legend_elements.append(
            Line2D([0], [0], color=FIELD_COLORS[field], linewidth=2.0,
                   label=FIELD_LABELS[field])
        )
    # Faction styles from the first variant (they should be the same across variants)
    first_fdata = variant_results[0]["faction_data"]
    first_rcounts = variant_results[0].get("region_counts", {})
    if len(first_fdata) > 1:
        legend_elements.append(Line2D([0], [0], color="none", label=""))
        for fac_idx, (fac_label, fac_info) in enumerate(first_fdata.items()):
            style = FACTION_STYLES[fac_idx % len(FACTION_STYLES)]
            legend_elements.append(
                Line2D([0], [0], color="#c0c0c0", linewidth=style["lw"],
                       linestyle=style["ls"], label=fac_info["display_name"])
            )

    axes[-1].legend(handles=legend_elements, loc="upper right", fontsize=9,
                    facecolor=BG_OUTER, edgecolor="#404060", labelcolor="#c0c0c0")

    fig.suptitle(scenario_name, color="#e0e0e0", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return output_path


def make_field_comparison(scenario_name: str,
                          ticks_list: list,
                          faction_data: dict,
                          field: str,
                          output_path: str):
    """
    Single-field comparison: one line per faction for one field.
    Cleaner than the overlay when you want to compare e.g. just economy across 4 factions.
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor(BG_OUTER)
    ax.set_facecolor(BG_INNER)

    # Each faction gets its own color from a palette
    faction_colors = ["#e74c3c", "#2ecc71", "#3498db", "#f39c12", "#9b59b6", "#1abc9c"]

    for fac_idx, (fac_label, fac_info) in enumerate(faction_data.items()):
        values = fac_info["fields"].get(field, [])
        if not values:
            continue
        color = faction_colors[fac_idx % len(faction_colors)]
        display = fac_info["display_name"]
        ax.plot(ticks_list[:len(values)], values,
                color=color, linewidth=1.8, label=display, alpha=0.9)
        ax.annotate(f"{values[-1]:.1f}",
                    xy=(ticks_list[len(values)-1], values[-1]),
                    xytext=(8, 0), textcoords="offset points",
                    color=color, fontsize=9, fontweight="bold", va="center")

    max_tick = max(ticks_list)
    ax.set_xlim(0, max_tick + 20)
    ax.set_ylim(0, 105)
    ax.set_xlabel("Tick", color="#a0a0a0", fontsize=12)
    ax.set_ylabel(f"{FIELD_LABELS[field]} (0–100)", color="#a0a0a0", fontsize=12)
    ax.set_title(f"{scenario_name} — {FIELD_LABELS[field]} Comparison",
                 color="#e0e0e0", fontsize=13, fontweight="bold", pad=15)

    ax.tick_params(colors="#707070")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#404060")
    ax.spines["bottom"].set_color("#404060")
    ax.grid(True, alpha=0.15, color="#ffffff")
    ax.legend(loc="upper right", fontsize=10, facecolor=BG_OUTER,
              edgecolor="#404060", labelcolor="#c0c0c0")

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path
