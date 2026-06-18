"""MultiGuardCode: Framework Diagram Generation."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np


def draw_framework_diagram(save_path="framework_diagram.pdf"):
    fig, ax = plt.subplots(1, 1, figsize=(14, 6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis('off')

    color_source = '#1565C0'
    color_source_light = '#E3F2FD'
    color_tier = '#2E7D32'
    color_tier_light = '#E8F5E9'
    color_error = '#C62828'
    color_error_light = '#FFEBEE'

    # Pipeline stages
    stages = [
        {"x": 1.5, "label": "LLM\nGeneration", "desc": "Prompt-based\ncode synthesis"},
        {"x": 4.0, "label": "T1: Output\nFilter", "desc": "Length/repetition\nquality check"},
        {"x": 6.5, "label": "T2: AST\nValidate", "desc": "Code extraction +\nsyntax validation"},
        {"x": 9.0, "label": "T3: Test\nRepair", "desc": "Test-driven iterative\nregeneration"},
        {"x": 11.5, "label": "T4: Defect\nMonitor", "desc": "Global defect rate\nadaptive control"},
    ]

    box_width = 2.0
    box_height = 1.6
    y_mid = 3.0

    for i, stage in enumerate(stages):
        color = color_source_light if i == 0 else color_tier_light
        edge = color_source if i == 0 else color_tier

        rect = FancyBboxPatch(
            (stage["x"] - box_width / 2, y_mid - box_height / 2),
            box_width, box_height,
            boxstyle="round,pad=0.15",
            facecolor=color,
            edgecolor=edge,
            linewidth=2
        )
        ax.add_patch(rect)
        ax.text(stage["x"], y_mid + 0.2, stage["label"],
                ha='center', va='center', fontsize=11, fontweight='bold',
                color=color_source if i == 0 else color_tier)
        ax.text(stage["x"], y_mid - 0.55, stage["desc"],
                ha='center', va='center', fontsize=8,
                color='#424242')

    # Flow arrows between stages
    for i in range(len(stages) - 1):
        x_start = stages[i]["x"] + box_width / 2 + 0.05
        x_end = stages[i + 1]["x"] - box_width / 2 - 0.05

        ax.annotate('', xy=(x_end, y_mid),
                    xytext=(x_start, y_mid),
                    arrowprops=dict(arrowstyle='->', color='#424242',
                                    lw=2.5, connectionstyle='arc3,rad=0'))

        mid_x = (x_start + x_end) / 2
        ax.text(mid_x, y_mid - 0.3, f'S{i+2}',
                ha='center', va='center', fontsize=7,
                color='#757575', fontstyle='italic')

    # Feedback loop for T3
    ax.annotate('', xy=(stages[2]["x"] + 0.6, y_mid + box_height / 2 + 0.3),
                xytext=(stages[3]["x"] - 0.6, y_mid + box_height / 2 + 0.3),
                arrowprops=dict(arrowstyle='->', color=color_error,
                                lw=1.5, connectionstyle='arc3,rad=0.4'))
    ax.annotate('', xy=(stages[3]["x"] - 0.6, y_mid + box_height / 2 + 0.05),
                xytext=(stages[2]["x"] + 0.6, y_mid + box_height / 2 + 0.05),
                arrowprops=dict(arrowstyle='->', color=color_error,
                                lw=1.5, connectionstyle='arc3,rad=-0.4'))

    ax.text((stages[2]["x"] + stages[3]["x"]) / 2, y_mid + box_height / 2 + 0.55,
            'Failure\nFeedback', ha='center', va='center', fontsize=7,
            color=color_error, fontweight='bold')

    # Error elimination text below pipeline
    ax.text(1.5, y_mid - box_height / 2 - 0.65, 'Raw output\nmay contain errors',
            ha='center', va='center', fontsize=7, color=color_error)
    ax.text(11.5, y_mid - box_height / 2 - 0.65, 'Validated\nreliable code',
            ha='center', va='center', fontsize=7, color=color_tier)

    # Title
    ax.text(6.5, 5.5, 'MultiGuardCode: Multi-Tier Error Suppression Framework for LLM Code Generation',
            ha='center', va='center', fontsize=15, fontweight='bold',
            color='#212121')

    # Subtitle
    ax.text(6.5, 5.0, 'Four-stage pipeline: filter, validate, repair, and monitor generated code',
            ha='center', va='center', fontsize=10,
            color='#616161')

    fig.tight_layout(rect=[0, 0.02, 1, 0.95])

    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
    fig.savefig(save_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"Framework diagram saved: {save_path}")


if __name__ == "__main__":
    draw_framework_diagram("../paper/figures/framework_diagram.pdf")
