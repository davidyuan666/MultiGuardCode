#!/usr/bin/env python
"""CD4Code: Full Experiment Pipeline with Baselines and Ablation.

Usage:
    python run_all.py                              # Run all experiments
    python run_all.py --dataset humaneval            # HumanEval only
    python run_all.py --dataset mbpp                  # MBPP only
    python run_all.py --mode raw,cd4code              # Specific modes
    python run_all.py --max-problems 20               # Quick test
    python run_all.py --t4stress                      # Tier4 stress test

Modes: raw, selfdebug, t3only, t123, cd4code, t4stress
"""
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    DEFAULT_TEMPERATURE, DEFAULT_TOP_P,
    TIER4_CONSERVATIVE_TEMP, TIER4_CONSERVATIVE_TOPP,
    HUMANEVAL_PATH, MBPP_PATH, RESULTS_DIR, FIGURES_DIR,
)
from generate import create_client, generate_code, load_humaneval, load_mbpp
from suppressor import CD4CodeSuppressor
from baselines import RawBaseline, SelfDebugBaseline
from evaluate import ExperimentEvaluator
from plot import (
    plot_defect_density_curve, plot_tier_survival, plot_ablation_comparison
)


def _get_prompt_humaneval(problem):
    return problem.get("prompt", "")

def _get_prompt_mbpp(problem):
    text = problem.get("text", "")
    test_list = problem.get("test_list", [])
    prompt = (
        f"Write a Python function to solve the following task:\n\n"
        f"{text}\n\n"
        f"The function should pass these test cases:\n"
    )
    for t in test_list[:3]:
        prompt += f"  {t}\n"
    prompt += "\nReturn ONLY the Python code."
    return prompt

def _get_test_humaneval(problem):
    return problem.get("test", ""), problem.get("entry_point", "")

def _get_test_mbpp(problem):
    tests = problem.get("test_list", [])
    test_func_name = problem.get("test_setup_code", "")
    entry = problem.get("entry_point", problem.get("task_id", ""))
    code = ""
    if test_func_name:
        code += f"{test_func_name}\n\n"
    code += f"\n".join(tests)
    return code, entry


def _select_hardest(problems, test_fn, entry_fn, client, n=30):
    """Select n hardest problems by raw pass rate (quick evaluation)."""
    scores = []
    for idx, problem in enumerate(problems):
        prompt = _get_prompt_humaneval(problem)
        test_code, entry = test_fn(problem), entry_fn(problem)
        codes = generate_code(prompt, temperature=0.7, top_p=0.95, n=1, client=client)
        if not codes or not codes[0] or not codes[0].strip():
            scores.append((idx, True))
            continue
        sup = CD4CodeSuppressor()
        code = sup._extract_function_code(codes[0])
        import ast
        try:
            ast.parse(code)
        except SyntaxError:
            scores.append((idx, True))
            continue
        passed, _ = sup._run_tests(code, test_code, entry)
        scores.append((idx, not passed))
        if (idx + 1) % 10 == 0:
            print(f"  Difficulty scan: {idx + 1}/{len(problems)}")
    scores.sort(key=lambda x: x[1], reverse=True)
    selected = [problems[i] for i, _ in scores[:n]]
    print(f"  Selected {len(selected)} hardest problems")
    return selected


def _run_cd4code_mode(problems, prompt_fn, test_fn, entry_fn, client,
                      disabled_tiers=None, use_conservative_mode=False):
    """Run CD4Code with optional tier disabling for ablation."""
    mode_name = "CD4Code" if disabled_tiers is None else \
        ("T1+T2+T3" if disabled_tiers == [4] else
         ("T3-Only" if set(disabled_tiers) == {1, 2, 4} else
          f"Ablation:{disabled_tiers}"))
    print(f"\n--- {mode_name} ---")

    suppressor = CD4CodeSuppressor(disabled_tiers=disabled_tiers)
    evaluator = ExperimentEvaluator()
    defect_history = []
    temp = DEFAULT_TEMPERATURE
    top_p = DEFAULT_TOP_P

    for idx, problem in enumerate(problems):
        prompt = prompt_fn(problem)
        test_code, entry = test_fn(problem), entry_fn(problem)

        code = generate_code(prompt, temperature=temp, top_p=top_p,
                             n=1, client=client)
        if not code or not code[0] or not code[0].strip():
            suppressor.total_count += 1
            suppressor.record_failure()
            evaluator.add_result(idx, [""], [False])
            defect_history.append(suppressor.get_defect_ratio())
            continue
        code = code[0]

        result = suppressor.process(
            code, test_code=test_code, entry_point=entry,
            client=client, generate_fn=generate_code,
        )
        passed = result["success"]
        if passed:
            code = result["final_code"]
        defect_history.append(suppressor.get_defect_ratio())

        if use_conservative_mode and result["t4_conservative"]:
            temp = TIER4_CONSERVATIVE_TEMP
            top_p = TIER4_CONSERVATIVE_TOPP

        evaluator.add_result(idx, [code], [passed])

        if (idx + 1) % 5 == 0:
            metrics = evaluator.compute_metrics()
            print(f"  [{idx + 1}/{len(problems)}] Pass@1: {metrics['pass_at_1']:.3f}, "
                  f"FDD: {metrics['functional_defect_density']:.3f}")

    metrics = evaluator.compute_metrics()
    stats = suppressor.get_stats()
    stats["total"] = suppressor.total_count
    print(f"  Final: Pass@1={metrics['pass_at_1']:.3f}, "
          f"Pass@5={metrics['pass_at_5']:.3f}, "
          f"FDD={metrics['functional_defect_density']:.3f}")
    print(f"  Tier stats: {stats}")

    return {
        "config": mode_name,
        "metrics": metrics,
        "stats": stats,
        "defect_history": defect_history,
        "evaluator": evaluator,
    }


def _run_raw_mode(problems, prompt_fn, test_fn, entry_fn, client, mode_name="Raw"):
    print(f"\n--- {mode_name} ---")
    baseline = RawBaseline()
    evaluator = ExperimentEvaluator()
    defect_history = []

    for idx, problem in enumerate(problems):
        prompt = prompt_fn(problem)
        test_code, entry = test_fn(problem), entry_fn(problem)
        passed, _ = baseline.evaluate(
            client, generate_code, prompt, test_code, entry)
        evaluator.add_result(idx, [""], [passed])
        defect_history.append(1.0 - (baseline.passed / max(baseline.total, 1)))

        if (idx + 1) % 5 == 0:
            m = evaluator.compute_metrics()
            print(f"  [{idx + 1}/{len(problems)}] Pass@1: {m['pass_at_1']:.3f}, "
                  f"FDD: {m['functional_defect_density']:.3f}")

    metrics = evaluator.compute_metrics()
    stats = baseline.get_stats()
    print(f"  Final: Pass@1={metrics['pass_at_1']:.3f}, "
          f"Pass@5={metrics['pass_at_5']:.3f}, "
          f"FDD={metrics['functional_defect_density']:.3f}")
    print(f"  Stats: {stats}")
    return {
        "config": mode_name,
        "metrics": metrics,
        "stats": stats,
        "defect_history": defect_history,
        "evaluator": evaluator,
    }


def _run_selfdebug_mode(problems, prompt_fn, test_fn, entry_fn, client):
    print(f"\n--- Self-Debug ---")
    baseline = SelfDebugBaseline(max_rounds=3)
    evaluator = ExperimentEvaluator()
    defect_history = []

    for idx, problem in enumerate(problems):
        prompt = prompt_fn(problem)
        test_code, entry = test_fn(problem), entry_fn(problem)
        passed, _ = baseline.evaluate(
            client, generate_code, prompt, test_code, entry)
        evaluator.add_result(idx, [""], [passed])
        defect_history.append(1.0 - (baseline.passed / max(baseline.total, 1)))

        if (idx + 1) % 5 == 0:
            m = evaluator.compute_metrics()
            print(f"  [{idx + 1}/{len(problems)}] Pass@1: {m['pass_at_1']:.3f}, "
                  f"FDD: {m['functional_defect_density']:.3f}")

    metrics = evaluator.compute_metrics()
    stats = baseline.get_stats()
    print(f"  Final: Pass@1={metrics['pass_at_1']:.3f}, "
          f"Pass@5={metrics['pass_at_5']:.3f}, "
          f"FDD={metrics['functional_defect_density']:.3f}")
    print(f"  Stats: {stats}")
    return {
        "config": "Self-Debug",
        "metrics": metrics,
        "stats": stats,
        "defect_history": defect_history,
        "evaluator": evaluator,
    }


def run_experiments(args):
    client = create_client()
    os.makedirs(RESULTS_DIR, exist_ok=True)

    all_modes = ["raw", "selfdebug", "t3only", "t123", "cd4code", "t4stress"]
    if args.mode:
        modes = [m.strip() for m in args.mode.split(",")]
    else:
        modes = all_modes

    datasets = []
    if not args.dataset or args.dataset == "humaneval":
        datasets.append(("HumanEval", load_humaneval(HUMANEVAL_PATH),
                         _get_prompt_humaneval, _get_test_humaneval))
    if not args.dataset or args.dataset == "mbpp":
        datasets.append(("MBPP", load_mbpp(MBPP_PATH, n_samples=50),
                         _get_prompt_mbpp, _get_test_mbpp))

    if args.max_problems:
        for i in range(len(datasets)):
            name, probs, fn, tf = datasets[i]
            datasets[i] = (name, probs[:args.max_problems], fn, tf)

    all_results = {}

    for ds_name, problems, prompt_fn, test_fn in datasets:
        print(f"\n{'=' * 60}")
        print(f"Dataset: {ds_name} ({len(problems)} problems)")
        print(f"{'=' * 60}")

        if ds_name == "HumanEval":
            te_fn, en_fn = lambda p: _get_test_humaneval(p)[0], \
                           lambda p: _get_test_humaneval(p)[1]
        else:
            te_fn = lambda p: _get_test_mbpp(p)[0]
            en_fn = lambda p: _get_test_mbpp(p)[1]

        for mode in modes:
            # Skip Self-Debug and ablation on MBPP for efficiency
            if ds_name != "HumanEval" and mode not in ("raw", "cd4code"):
                continue
            # Tier4 stress only on HumanEval
            if mode == "t4stress" and ds_name != "HumanEval":
                continue
            # Mode-specific handling
            if mode == "t4stress" and "t4stress" in modes:
                print("\n  [Tier4 Stress] Selecting hardest problems...")
                hard_problems = _select_hardest(problems, te_fn, en_fn, client, n=30)
                print(f"  [Tier4 Stress] Running on {len(hard_problems)} hard problems...")
                result = _run_cd4code_mode(
                    hard_problems, prompt_fn, te_fn, en_fn, client,
                    disabled_tiers=None, use_conservative_mode=True
                )
                key = f"{ds_name}_T4Stress"
            elif mode == "raw":
                result = _run_raw_mode(problems, prompt_fn, te_fn, en_fn, client, "Raw")
                key = f"{ds_name}_Raw"
            elif mode == "selfdebug":
                result = _run_selfdebug_mode(problems, prompt_fn, te_fn, en_fn, client)
                key = f"{ds_name}_SelfDebug"
            elif mode == "t3only":
                result = _run_cd4code_mode(
                    problems, prompt_fn, te_fn, en_fn, client,
                    disabled_tiers=[1, 2, 4], use_conservative_mode=False
                )
                key = f"{ds_name}_T3Only"
            elif mode == "t123":
                result = _run_cd4code_mode(
                    problems, prompt_fn, te_fn, en_fn, client,
                    disabled_tiers=[4], use_conservative_mode=False
                )
                key = f"{ds_name}_T123"
            elif mode == "cd4code":
                result = _run_cd4code_mode(
                    problems, prompt_fn, te_fn, en_fn, client,
                    disabled_tiers=None, use_conservative_mode=True
                )
                key = f"{ds_name}_CD4Code"
            else:
                continue

            all_results[key] = result
            result_path = os.path.join(RESULTS_DIR, f"{key}.json")
            result["evaluator"].save_results(result_path)

    print("\n" + "=" * 60)
    print("Generating figures...")
    print("=" * 60)

    try:
        os.makedirs(FIGURES_DIR, exist_ok=True)

        # Defect density curves
        for ds_name, _, _, _ in datasets:
            raw_key = f"{ds_name}_Raw"
            cd4code_key = f"{ds_name}_CD4Code"
            if raw_key in all_results and cd4code_key in all_results:
                fig_path = os.path.join(FIGURES_DIR, f"{ds_name}_defect_density_curve.pdf")
                plot_defect_density_curve(
                    all_results[raw_key]["defect_history"],
                    all_results[cd4code_key]["defect_history"],
                    fig_path
                )

        # Tier survival
        cd4code_key = f"{datasets[0][0]}_CD4Code"
        if cd4code_key in all_results:
            fig_path = os.path.join(FIGURES_DIR, "tier_survival.pdf")
            plot_tier_survival(all_results[cd4code_key]["stats"], fig_path)

        # Ablation comparison
        ablation_data = {v["config"]: v["metrics"] for k, v in all_results.items()
                        if k.startswith(datasets[0][0])}
        if ablation_data:
            fig_path = os.path.join(FIGURES_DIR, "ablation_comparison.pdf")
            plot_ablation_comparison(ablation_data, fig_path)

        # Framework diagram
        from framework_diagram import draw_framework_diagram
        draw_framework_diagram(os.path.join(FIGURES_DIR, "framework_diagram.pdf"))

        print("\nFigures generated in:", FIGURES_DIR)
    except Exception as e:
        print(f"Warning: figure generation failed: {e}")

    summary_path = os.path.join(RESULTS_DIR, "summary.json")
    summary = {k: {"config": v["config"], "metrics": v["metrics"], "stats": v["stats"]}
               for k, v in all_results.items()}
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSummary saved: {summary_path}")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="CD4Code Experiment Pipeline")
    parser.add_argument("--dataset", choices=["humaneval", "mbpp"],
                       help="Run specific dataset only")
    parser.add_argument("--mode", type=str,
                       help="Comma-separated modes: raw,selfdebug,t3only,t123,cd4code,t4stress")
    parser.add_argument("--max-problems", type=int,
                       help="Limit number of problems")
    parser.add_argument("--t4stress", action="store_true",
                       help="Include Tier4 stress test")
    args = parser.parse_args()
    if args.t4stress:
        args.mode = "t4stress" if not args.mode else args.mode + ",t4stress"
    run_experiments(args)


if __name__ == "__main__":
    main()
