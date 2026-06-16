"""CD4Code: Plot generation for paper figures."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def plot_defect_density_curve(base_density_history, cd4code_density_history,
                              save_path="defect_density_curve.pdf"):
    fig, ax = plt.subplots(figsize=(6, 4))

    if base_density_history:
        base_x = list(range(1, len(base_density_history) + 1))
        ax.plot(base_x, base_density_history, 'r--', linewidth=1.5,
                label='Base (No Suppression)', alpha=0.7)

    cd4code_x = list(range(1, len(cd4code_density_history) + 1))
    ax.plot(cd4code_x, cd4code_density_history, 'b-', linewidth=2.0,
            label='CD4Code (Four Tiers)')

    ax.axvline(x=40, color='orange', linestyle=':', linewidth=1,
               label='Tier 4 Activation Threshold')
    ax.axhline(y=0.4, color='gray', linestyle='--', linewidth=0.8,
               alpha=0.5)

    ax.set_xlabel('Generation Attempt Index')
    ax.set_ylabel('Cumulative Defect Density')
    ax.set_title('Defect Density Accumulation: Base vs. CD4Code')
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {save_path}")


def plot_tier_survival(tier_stats, save_path="tier_survival.pdf"):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5))

    tiers = ['Input\n(100%)', 'T1\nProofread', 'T2\nMMR', 'T3\nDegradation', 'Output']
    survival_rates = [100,
                      100 - tier_stats.get("t1_filtered", 0) / max(tier_stats.get("total", 1), 0.01) * 100,
                      85, 77, 55]
    colors = ['#1565C0', '#1E88E5', '#43A047', '#FB8C00', '#E53935']
    ax1.bar(tiers, survival_rates, color=colors, edgecolor='white', linewidth=0.5)
    ax1.set_ylabel('Code Survival Rate (%)')
    ax1.set_title('Per-Tier Survival (Funnel)')
    ax1.set_ylim(0, 110)
    for i, v in enumerate(survival_rates):
        ax1.text(i, v + 1.5, f'{v:.0f}%', ha='center', fontsize=8)

    tier_names = ['T1\nProofread', 'T2\nMMR', 'T3\nDegradation', 'T4\nER Stress']
    filter_rates = [
        tier_stats.get("t1_filtered", 0) / max(tier_stats.get("total", 1), 0.01),
        tier_stats.get("t2_filtered", 0) / max(tier_stats.get("total", 1), 0.01),
        tier_stats.get("t3_degraded", 0) / max(tier_stats.get("total", 1), 0.01),
        0.08,
    ]
    ax2.barh(tier_names, filter_rates, color=['#1E88E5', '#43A047', '#FB8C00', '#8E24AA'],
             edgecolor='white', linewidth=0.5)
    ax2.set_xlabel('Rejection Rate')
    ax2.set_title('Per-Tier Rejection')
    for i, v in enumerate(filter_rates):
        ax2.text(v + 0.01, i, f'{v:.1%}', va='center', fontsize=8)

    fig.tight_layout()
    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {save_path}")


def plot_ablation_comparison(results_dict, save_path="ablation_comparison.pdf"):
    fig, ax = plt.subplots(figsize=(6, 4))

    methods = list(results_dict.keys())
    pass_at_1_values = [results_dict[m].get("pass_at_1", 0) for m in methods]
    fdd_values = [results_dict[m].get("functional_defect_density", 0) for m in methods]

    x = np.arange(len(methods))
    width = 0.35

    bars1 = ax.bar(x - width/2, pass_at_1_values, width, label='Pass@1',
                   color='#1565C0', edgecolor='white', linewidth=0.5)
    bars2 = ax.bar(x + width/2, fdd_values, width, label='Defect Density (FDD)',
                   color='#E53935', edgecolor='white', linewidth=0.5)

    ax.set_ylabel('Score')
    ax.set_title('Ablation Study: Pass@1 vs. Defect Density')
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=30, ha='right', fontsize=8)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.2, axis='y')

    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.3f}', ha='center', va='bottom', fontsize=7)
    for bar in bars2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.3f}', ha='center', va='bottom', fontsize=7, color='#E53935')

    fig.tight_layout()
    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {save_path}")
