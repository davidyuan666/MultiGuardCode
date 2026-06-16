"""CD4Code: Four-Tier Error Suppression Framework."""
import ast
import subprocess
import tempfile
import os
import re
from config import (
    TIER1_CONFIDENCE_THRESHOLD, TIER2_LINTER, TIER2_TYPE_CHECKER,
    TIER3_MAX_RETRIES, TIER4_DEFECT_THRESHOLD,
    TIER4_CONSERVATIVE_TEMP, TIER4_CONSERVATIVE_TOPP
)


class CD4CodeSuppressor:
    def __init__(self):
        self.tier1_threshold = TIER1_CONFIDENCE_THRESHOLD
        self.tier4_threshold = TIER4_DEFECT_THRESHOLD
        self.failure_count = 0
        self.total_count = 0
        self.tier_stats = {"t1_filtered": 0, "t2_filtered": 0,
                          "t3_degraded": 0, "t4_activated": 0}

    def tier1_proofreading(self, code):
        """Token-level confidence filtering (DNA Polymerase Proofreading analog).

        Rejects code with obviously malformed patterns that low-confidence
        token sampling would produce: extreme repetition, empty blocks, etc.
        """
        if not code or len(code.strip()) < 20:
            self.tier_stats["t1_filtered"] += 1
            return None

        lines = code.strip().split('\n')

        # Reject if > 60% of lines are just whitespace/empty
        empty_ratio = sum(1 for l in lines if not l.strip()) / max(len(lines), 1)
        if empty_ratio > 0.6:
            self.tier_stats["t1_filtered"] += 1
            return None

        # Reject extreme line repetition pattern (> 5 identical consecutive lines)
        for i in range(len(lines) - 5):
            if len(set(lines[i:i+5])) == 1 and lines[i].strip():
                self.tier_stats["t1_filtered"] += 1
                return None

        return code

    def tier2_mismatch_repair(self, code):
        """Structural static analysis (Mismatch Repair analog).

        Checks syntax validity via AST parsing.
        """
        try:
            ast.parse(code)
        except SyntaxError as e:
            self.tier_stats["t2_filtered"] += 1
            return None, str(e)

        return code, None

    def _extract_function_code(self, code, entry_point=None):
        code = code.strip()
        code = re.sub(r'^```(?:python)?\s*\n?', '', code)
        code = re.sub(r'\n?```\s*$', '', code)
        code = code.replace('\r\n', '\n')
        return code

    def tier3_test_degradation(self, code, test_code, entry_point, client=None, generate_fn=None):
        """Test-driven discard and regeneration (Ubiquitin-Proteasome analog)."""
        code = self._extract_function_code(code)

        for attempt in range(TIER3_MAX_RETRIES):
            passed, error_msg = self._run_tests(code, test_code, entry_point)
            if passed:
                return code, True

            if attempt < TIER3_MAX_RETRIES - 1 and client and generate_fn:
                fix_prompt = (
                    f"The following Python code failed tests:\n\n```python\n{code}\n```\n\n"
                    f"Error: {error_msg}\n\n"
                    f"Write the corrected version of the code. Return ONLY the code."
                )
                new_code = generate_fn(fix_prompt, client=client)
                if new_code:
                    code = self._extract_function_code(new_code)

        self.tier_stats["t3_degraded"] += 1
        return None, False

    def _run_tests(self, code, test_code, entry_point):
        full_code = f"{code}\n\n{test_code}\n\n"
        if entry_point:
            full_code += f"if __name__ == '__main__':\n"
            full_code += f"    test_{entry_point}()\n" if entry_point else "    pass\n"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False,
                                         encoding='utf-8') as f:
            f.write(full_code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                ['python', tmp_path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return True, None
            return False, result.stderr[:500] if result.stderr else result.stdout[:500]
        except subprocess.TimeoutExpired:
            return False, "Execution timed out"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def tier4_global_monitor(self):
        """Global defect density monitoring (ER Stress Response analog).

        Returns True if conservative mode should be activated.
        """
        self.total_count += 1
        ratio = self.failure_count / max(self.total_count, 1)
        if ratio >= self.tier4_threshold and self.total_count > 10:
            self.tier_stats["t4_activated"] += 1
            return True
        return False

    def record_failure(self):
        self.failure_count += 1

    def process(self, code, test_code=None, entry_point=None,
                client=None, generate_fn=None):
        """Apply all four CD4Code tiers to a generated code sample."""
        result = {
            "original_code": code,
            "passed_t1": False,
            "passed_t2": False,
            "passed_t3": False,
            "t4_conservative": False,
            "final_code": None,
            "success": False,
        }

        code = self.tier1_proofreading(code)
        if code is None:
            return result
        result["passed_t1"] = True

        code, syntax_error = self.tier2_mismatch_repair(code)
        if code is None:
            return result
        result["passed_t2"] = True

        if test_code:
            code, passed = self.tier3_test_degradation(
                code, test_code, entry_point, client, generate_fn
            )
            if not passed:
                self.record_failure()
                return result
            result["passed_t3"] = True

        result["t4_conservative"] = self.tier4_global_monitor()
        result["final_code"] = code
        result["success"] = True
        return result

    def get_stats(self):
        return self.tier_stats.copy()

    def get_defect_ratio(self):
        return self.failure_count / max(self.total_count, 1)
