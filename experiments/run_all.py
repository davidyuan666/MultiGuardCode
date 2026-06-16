#!/usr/bin/env python
"""CD4Code: Full Experiment Pipeline.

Usage:
    python run_all.py                    # Run all experiments
    python run_all.py --dataset humaneval  # HumanEval only
    python run_all.py --skip-generate      # Use cached results
    python run_all.py --max-problems 20    # Quick test run
"""
import os
import sys
import json
import time
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    DEFAULT_TEMPERATURE, DEFAULT_TOP_P,
    TIER4_CONSERVATIVE_TEMP, TIER4_CONSERVATIVE_TOPP,
    HUMANEVAL_PATH, MBPP_PATH, RESULTS_DIR, FIGURES_DIR,
)
from generate import create_client, generate_code, load_humaneval, load_mbpp
from suppressor import CD4CodeSuppressor
from evaluate import ExperimentEvaluator
from plot import (
    plot_defect_density_curve, plot_tier_survival, plot_ablation_comparison
)


def get_prompt_humaneval(problem):
    return problem.get("prompt", "")


def get_prompt_mbpp(problem):
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


def get_test_code_humaneval(problem):
    return problem.get("test", "")


def get_test_code_mbpp(problem):
    tests = problem.get("test_list", [])
    test_func_name = problem.get("test_setup_code", "")
    entry = problem.get("entry_point", problem.get("task_id", ""))
    code = ""
    if test_func_name:
        code += f"{test_func_name}\n\n"
    code += f"\n".join(tests)
    return code, entry


def run_experiments(args):
    client = create_client()
    os.makedirs(RESULTS_DIR, exist_ok=True)

    datasets = []
    if not args.dataset or args.dataset == "humaneval":
        datasets.append(("HumanEval", load_humaneval(HUMANEVAL_PATH), get_prompt_humaneval))
    if not args.dataset or args.dataset == "mbpp":
        datasets.append(("MBPP", load_mbpp(MBPP_PATH, n_samples=50), get_prompt_mbpp))

    if args.max_problems:
        for i in range(len(datasets)):
            name, probs, fn = datasets[i]
            datasets[i] = (name, probs[:args.max_problems], fn)

    all_results = {}

    for ds_name, problems, prompt_fn in datasets:
        print(f"\n{'=' * 60}")
        print(f"Dataset: {ds_name} ({len(problems)} problems)")
        print(f"{'=' * 60}")

        if ds_name == "HumanEval":
            test_fn = get_test_code_humaneval
            entry_fn = lambda p: p.get("entry_point", "")
        else:
            test_fn = lambda p: get_test_code_mbpp(p)[0]
            entry_fn = lambda p: get_test_code_mbpp(p)[1]

        suppressors = {
            "Base": (CD4CodeSuppressor(), False),
            "CD4Code": (CD4CodeSuppressor(), True),
        }

        for method_name, (suppressor, use_suppression) in suppressors.items():
            print(f"\n--- {method_name} ---")
            evaluator = ExperimentEvaluator()
            defect_history = []
            base_history = []

            temp = DEFAULT_TEMPERATURE
            top_p = DEFAULT_TOP_P

            suppress_tiers = method_name == "CD4Code"

            for idx, problem in enumerate(problems):
                prompt = prompt_fn(problem)
                test_code = test_fn(problem)
                entry = entry_fn(problem)

                code = generate_code(prompt, temperature=temp, top_p=top_p,
                                     n=1, client=client)
                if not code or not code[0]:
                    evaluator.add_result(idx, [code], [False])
                    continue
                code = code[0]

                passed = False
                if suppress_tiers:
                    result = suppressor.process(
                        code, test_code=test_code, entry_point=entry,
                        client=client, generate_fn=generate_code,
                    )
                    if result["success"]:
                        passed = True
                        code = result["final_code"]
                    defect_history.append(suppressor.get_defect_ratio())

                    if result["t4_conservative"]:
                        temp = TIER4_CONSERVATIVE_TEMP
                        top_p = TIER4_CONSERVATIVE_TOPP
                else:
                    result = suppressor.process(code, test_code=None)
                    if result["passed_t1"]:
                        result2 = suppressor.process(code, test_code=test_code,
                                                      entry_point=entry,
                                                      client=client,
                                                      generate_fn=generate_code)
                        passed = result2["success"]
                    defect_history.append(suppressor.get_defect_ratio())

                evaluator.add_result(idx, [code], [passed])

                if (idx + 1) % 5 == 0:
                    metrics = evaluator.compute_metrics()
                    print(f"  [{idx + 1}/{len(problems)}] Pass@1: {metrics['pass_at_1']:.3f}, "
                          f"FDD: {metrics['functional_defect_density']:.3f}")

            metrics = evaluator.compute_metrics()
            stats = suppressor.get_stats()
            stats["total"] = suppressor.total_count

            print(f"\n  Final: Pass@1={metrics['pass_at_1']:.3f}, "
                  f"Pass@5={metrics['pass_at_5']:.3f}, "
                  f"FDD={metrics['functional_defect_density']:.3f}")
            print(f"  Tier stats: {stats}")

            result_path = os.path.join(RESULTS_DIR, f"{ds_name}_{method_name}.json")
            evaluator.save_results(result_path)

            all_results[f"{ds_name}_{method_name}"] = {
                "metrics": metrics,
                "stats": stats,
                "defect_history": defect_history,
            }

    print("\n" + "=" * 60)
    print("Generating figures...")
    print("=" * 60)

    try:
        os.makedirs(FIGURES_DIR, exist_ok=True)

        for ds_name, _, _ in datasets:
            cd4code_defect = all_results[f"{ds_name}_CD4Code"]["defect_history"]
            base_defect = all_results[f"{ds_name}_Base"]["defect_history"]
            fig_path = os.path.join(FIGURES_DIR, f"{ds_name}_defect_density_curve.pdf")
            plot_defect_density_curve(base_defect, cd4code_defect, fig_path)

        cd4code_stats = all_results[f"{datasets[0][0]}_CD4Code"]["stats"]
        fig_path = os.path.join(FIGURES_DIR, "tier_survival.pdf")
        plot_tier_survival(cd4code_stats, fig_path)

        ablation_data = {}
        for key in all_results:
            name = key.split("_", 1)[1] if "_" in key else key
            ablation_data[name] = all_results[key]["metrics"]
        fig_path = os.path.join(FIGURES_DIR, "ablation_comparison.pdf")
        plot_ablation_comparison(ablation_data, fig_path)

        print("\nFigures generated in:", FIGURES_DIR)
    except Exception as e:
        print(f"Warning: figure generation failed: {e}")

    summary_path = os.path.join(RESULTS_DIR, "summary.json")
    summary = {k: v["metrics"] for k, v in all_results.items()}
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSummary saved: {summary_path}")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="CD4Code Experiment Pipeline")
    parser.add_argument("--dataset", choices=["humaneval", "mbpp"],
                       help="Run specific dataset only")
    parser.add_argument("--max-problems", type=int,
                       help="Limit number of problems (for quick testing)")
    args = parser.parse_args()
    run_experiments(args)


if __name__ == "__main__":
    main()
