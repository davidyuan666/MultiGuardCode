"""CD4Code: Framework Diagram Generation."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np


def draw_framework_diagram(save_path="framework_diagram.pdf"):
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Colors
    color_bio = '#1565C0'       # blue for biology
    color_bio_light = '#E3F2FD'
    color_code = '#E65100'      # orange for code generation
    color_code_light = '#FFF3E0'
    color_tier = '#2E7D32'      # green for tier labels
    color_error = '#C62828'     # red for error arrows

    # Column positions
    left_col = 1.3
    mid_col = 4.0
    right_col = 6.7
    box_width = 2.2
    box_height = 1.1
    tier_width = 1.0

    # Y positions for each row
    y_positions = [8.2, 6.2, 4.2, 2.2]

    # Row labels
    bio_labels = ['DNA\nReplication', 'Transcription\n(mRNA)', 'Translation\n(Protein)', 'Post-Translational\nQC']
    bio_mechanisms = ['Polymerase\nProofreading', 'Mismatch Repair\n(MMR)', 'Ubiquitin-Proteasome\nDegradation', 'ER Stress\nResponse (UPR)']
    code_labels = ['Prompt →\nToken Generation', 'Token Sequence\n→ AST Formation', 'AST → Code\nExecution', 'Global\nDefect Monitor']
    tier_labels = ['Tier 1\nProofread', 'Tier 2\nMMR', 'Tier 3\nDegradation', 'Tier 4\nUPR']

    # Draw boxes
    for i in range(4):
        y = y_positions[i]

        # Biology box
        rect_bio = FancyBboxPatch(
            (left_col - box_width / 2, y - box_height / 2),
            box_width, box_height,
            boxstyle="round,pad=0.1",
            facecolor=color_bio_light,
            edgecolor=color_bio,
            linewidth=2
        )
        ax.add_patch(rect_bio)
        ax.text(left_col, y, bio_labels[i],
                ha='center', va='center', fontsize=10, fontweight='bold',
                color=color_bio)

        # Arrow: bio -> mechanism (center column)
        ax.annotate('', xy=(mid_col - tier_width / 2 - 0.1, y),
                    xytext=(left_col + box_width / 2 + 0.1, y),
                    arrowprops=dict(arrowstyle='->', color=color_bio,
                                    lw=2, connectionstyle='arc3,rad=0'))

        # Mechanism label (center column)
        ax.text(mid_col, y, bio_mechanisms[i],
                ha='center', va='center', fontsize=8,
                bbox=dict(boxstyle='round', facecolor='#F5F5F5',
                          edgecolor='#BDBDBD', alpha=0.8))

        # Arrow: mechanism -> code
        ax.annotate('', xy=(right_col - box_width / 2 - 0.1, y),
                    xytext=(mid_col + 0.5, y),
                    arrowprops=dict(arrowstyle='->', color=color_tier,
                                    lw=2, connectionstyle='arc3,rad=0'))

        # Code generation box
        rect_code = FancyBboxPatch(
            (right_col - box_width / 2, y - box_height / 2),
            box_width, box_height,
            boxstyle="round,pad=0.1",
            facecolor=color_code_light,
            edgecolor=color_code,
            linewidth=2
        )
        ax.add_patch(rect_code)
        ax.text(right_col, y, code_labels[i],
                ha='center', va='center', fontsize=9, fontweight='bold',
                color=color_code)

        # Tier badge (right of code box)
        tier_x = right_col + box_width / 2 + 0.6
        ax.text(tier_x, y, tier_labels[i],
                ha='center', va='center', fontsize=8, fontweight='bold',
                color='white',
                bbox=dict(boxstyle='circle,pad=0.3',
                          facecolor=color_tier, edgecolor='none'))

    # Vertical flow arrows between tiers
    for i in range(3):
        y_top = y_positions[i] - box_height / 2
        y_bot = y_positions[i + 1] + box_height / 2
        # Right side: Code generation flow
        ax.annotate('', xy=(right_col, y_bot + 0.15),
                    xytext=(right_col, y_top - 0.15),
                    arrowprops=dict(arrowstyle='->', color=color_code,
                                    lw=2.5))
        # Left side: Biological flow
        ax.annotate('', xy=(left_col, y_bot + 0.15),
                    xytext=(left_col, y_top - 0.15),
                    arrowprops=dict(arrowstyle='->', color=color_bio,
                                    lw=2.5))

    # Error accumulation indicator on the right side
    error_x = 9.2
    for i in range(4):
        y = y_positions[i]
        # Draw small error rate indicator
        error_rates = [1e-1, 1e-2, 1e-4, 1e-8]
        ax.text(error_x, y, f'ε ≈ {error_rates[i]:.0e}\nresidual',
                ha='center', va='center', fontsize=7,
                color=color_error,
                bbox=dict(boxstyle='round', facecolor='#FFEBEE',
                          edgecolor=color_error, alpha=0.7))

    # Column headers
    header_y = 9.4
    ax.text(left_col, header_y, 'Biology\n(Central Dogma)',
            ha='center', va='center', fontsize=13, fontweight='bold',
            color=color_bio)
    ax.text(mid_col, header_y, 'Quality Control\nMechanism',
            ha='center', va='center', fontsize=11, fontweight='bold',
            color='#424242')
    ax.text(right_col, header_y, 'Code Generation\nPipeline',
            ha='center', va='center', fontsize=13, fontweight='bold',
            color=color_code)

    # Legend for colors (bottom)
    ax.text(1.0, 0.6, '■ Biology\t■ QC Mechanism\t■ Code Gen\t● Tiers\t■ Error Rate',
            fontsize=7, color='#616161', ha='left')

    # Title
    ax.text(5.0, 9.9, 'CD4Code: A Central Dogma-Inspired Multi-Tier Error Suppression Framework',
            ha='center', va='center', fontsize=16, fontweight='bold',
            color='#212121')

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])

    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
    fig.savefig(save_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"Framework diagram saved: {save_path}")


if __name__ == "__main__":
    draw_framework_diagram("../paper/figures/framework_diagram.pdf")
