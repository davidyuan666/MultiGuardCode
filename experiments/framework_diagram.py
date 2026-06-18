"""MultiGuardCode: Framework Diagram Generation."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np


def draw_framework_diagram(save_path="framework_diagram.pdf"):
    fig, ax = plt.subplots(1, 1, figsize=(5, 9.5))
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 10)
    ax.axis('off')

    color_source = '#1565C0'
    color_source_light = '#E3F2FD'
    color_tier = '#2E7D32'
    color_tier_light = '#E8F5E9'
    color_error = '#C62828'

    box_width = 4.2
    box_height = 1.0
    x_center = 2.5

    stages = [
        {"y": 8.1, "label": "LLM Generation", "desc": "Prompt-based code synthesis via DeepSeek V4 Pro"},
        {"y": 6.7, "label": "T1: Output Filter", "desc": "Length check + repetition detection"},
        {"y": 5.3, "label": "T2: AST Validate", "desc": "Code extraction + syntax validation"},
        {"y": 3.9, "label": "T3: Test Repair", "desc": "Test-driven iterative regeneration (3 retries)"},
        {"y": 2.5, "label": "T4: Defect Monitor", "desc": "Global defect rate monitoring + adaptive params"},
    ]

    for i, stage in enumerate(stages):
        color = color_source_light if i == 0 else color_tier_light
        edge = color_source if i == 0 else color_tier
        y = stage["y"]

        rect = FancyBboxPatch(
            (x_center - box_width / 2, y - box_height / 2),
            box_width, box_height,
            boxstyle="round,pad=0.15",
            facecolor=color,
            edgecolor=edge,
            linewidth=2.5
        )
        ax.add_patch(rect)
        ax.text(x_center, y + 0.12, stage["label"],
                ha='center', va='center', fontsize=14, fontweight='bold',
                color=color_source if i == 0 else color_tier)
        ax.text(x_center, y - 0.26, stage["desc"],
                ha='center', va='center', fontsize=9,
                color='#424242')

    for i in range(len(stages) - 1):
        y_start = stages[i]["y"] - box_height / 2
        y_end = stages[i + 1]["y"] + box_height / 2
        ax.annotate('', xy=(x_center, y_end + 0.05),
                    xytext=(x_center, y_start - 0.05),
                    arrowprops=dict(arrowstyle='->', color='#424242',
                                    lw=2.5, connectionstyle='arc3,rad=0'))
        mid_y = (y_start + y_end) / 2
        ax.text(x_center + 0.35, mid_y, f'S{i+2}',
                ha='center', va='center', fontsize=8,
                color='#757575', fontstyle='italic')

    y_repair = stages[3]["y"]
    ax.annotate('', xy=(x_center + box_width / 2 + 0.4, y_repair + 0.4),
                xytext=(x_center + box_width / 2 + 0.4, y_repair - 0.4),
                arrowprops=dict(arrowstyle='->', color=color_error,
                                lw=1.8, connectionstyle='arc3,rad=-0.3'))
    ax.annotate('', xy=(x_center + box_width / 2 + 0.05, y_repair + 0.4),
                xytext=(x_center + box_width / 2 + 0.05, y_repair - 0.4),
                arrowprops=dict(arrowstyle='->', color=color_error,
                                lw=1.8, connectionstyle='arc3,rad=0.3'))
    ax.text(x_center + box_width / 2 + 0.65, y_repair,
            'Retry\nLoop', ha='center', va='center', fontsize=8,
            color=color_error, fontweight='bold')

    ax.text(x_center, 1.0, 'Validated Reliable Code',
            ha='center', va='center', fontsize=11,
            color=color_tier, fontweight='bold')
    ax.text(x_center, 9.0, 'Raw LLM Output (may contain errors)',
            ha='center', va='center', fontsize=10,
            color=color_error)

    ax.text(2.5, 9.72, 'MultiGuardCode: Multi-Tier Error',
            ha='center', va='center', fontsize=18, fontweight='bold',
            color='#212121')
    ax.text(2.5, 9.35, 'Suppression Framework for LLM Code Generation',
            ha='center', va='center', fontsize=12, fontweight='bold',
            color='#424242')

    fig.tight_layout(rect=[0.02, 0.01, 0.98, 0.97])

    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
    fig.savefig(save_path, dpi=250, bbox_inches='tight')
    plt.close(fig)
    print(f"Framework diagram saved: {save_path}")


if __name__ == "__main__":
    draw_framework_diagram("../paper/figures/framework_diagram.pdf")
