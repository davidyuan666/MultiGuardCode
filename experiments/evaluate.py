"""CD4Code: Evaluation and Metrics."""
import json
import os
from datetime import datetime


def compute_pass_at_k(n, c, k):
    """Unbiased estimator of Pass@k (Chen et al., 2021)."""
    if n - c < k:
        return 1.0
    return 1.0 - (float(_comb(n - c, k)) / float(_comb(n, k)))


def _comb(n, k):
    if k > n or k < 0:
        return 0
    k = min(k, n - k)
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result


class ExperimentEvaluator:
    def __init__(self, n_samples=1):
        self.n_samples = n_samples
        self.results = []

    def add_result(self, problem_id, samples, passed):
        self.results.append({
            "problem_id": problem_id,
            "n_samples": len(samples),
            "n_passed": sum(1 for p in passed if p),
            "passed_list": passed,
        })

    def compute_metrics(self):
        total = len(self.results)
        correct_at_1 = sum(1 for r in self.results if r["passed_list"][0]) if self.results else 0

        pass_at_1 = correct_at_1 / max(total, 1)

        all_n = [r["n_samples"] for r in self.results]
        all_c = [r["n_passed"] for r in self.results]
        pass_at_5_vals = []
        for n, c in zip(all_n, all_c):
            if n >= 5:
                val = compute_pass_at_k(n, c, 5)
            else:
                val = 1.0 if c > 0 else 0.0
            pass_at_5_vals.append(val)
        pass_at_5 = sum(pass_at_5_vals) / max(len(pass_at_5_vals), 1)

        defect_density = 1.0 - (sum(r["n_passed"] for r in self.results) /
                                max(sum(r["n_samples"] for r in self.results), 1))

        return {
            "total_problems": total,
            "pass_at_1": round(pass_at_1, 4),
            "pass_at_5": round(pass_at_5, 4),
            "functional_defect_density": round(defect_density, 4),
        }

    def save_results(self, filepath):
        metrics = self.compute_metrics()
        output = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "details": self.results,
        }
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        return metrics
