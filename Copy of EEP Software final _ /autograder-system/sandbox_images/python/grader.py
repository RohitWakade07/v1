import json
import sys
import subprocess
import time

RESULTS_PATH = "/autograder/results/results.json"


def write_results(payload: dict) -> None:
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def main():
    start_time = time.time()

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_hidden.py",
                "-q",
                "--tb=short",
                "--json-report",
                "--json-report-file=/tmp/report.json",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        report_data = {}
        try:
            with open("/tmp/report.json", "r", encoding="utf-8") as f:
                report_data = json.load(f)
        except Exception:
            report_data = {}

        summary = report_data.get("summary", {})
        total_tests = summary.get("total", 0)
        passed_tests = summary.get("passed", 0)

        tests_list = []
        for test in report_data.get("tests", []):
            name = test.get("nodeid", "").split("::")[-1] or "unknown_test"
            outcome = test.get("outcome", "failed")
            message = None

            if outcome != "passed":
                call = test.get("call", {})
                crash = call.get("crash", {})
                message = crash.get("message") or "Test failed"

            tests_list.append(
                {
                    "name": name[:200],
                    "passed": outcome == "passed",
                    "message": message[:1000] if message else None,
                }
            )

        execution_time_ms = int((time.time() - start_time) * 1000)

        if total_tests == 0:
            results = {
                "score": 0,
                "status": "failed",
                "feedback": f"Tests did not run correctly.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"[:5000],
                "tests": [],
                "execution_time_ms": execution_time_ms,
            }
        else:
            score = round((passed_tests / total_tests) * 100, 2)
            all_passed = passed_tests == total_tests and result.returncode == 0

            results = {
                "score": score,
                "status": "completed" if all_passed else "failed",
                "feedback": (
                    f"Passed {passed_tests}/{total_tests} tests."
                    if all_passed
                    else f"Passed {passed_tests}/{total_tests} tests. Some hidden tests failed."
                )[:5000],
                "tests": tests_list,
                "execution_time_ms": execution_time_ms,
            }

    except subprocess.TimeoutExpired:
        results = {
            "score": 0,
            "status": "failed",
            "feedback": "Execution Timeout: Student code took too long during testing.",
            "tests": [],
            "execution_time_ms": int((time.time() - start_time) * 1000),
        }
    except Exception as e:
        results = {
            "score": 0,
            "status": "failed",
            "feedback": f"Internal Sandbox Error: {str(e)}"[:5000],
            "tests": [],
            "execution_time_ms": int((time.time() - start_time) * 1000),
        }

    try:
        write_results(results)
    except Exception as e:
        print(f"Failed to write results.json: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
