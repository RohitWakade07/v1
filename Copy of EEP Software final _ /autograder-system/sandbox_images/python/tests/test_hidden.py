import sys

sys.path.append("/autograder/submission")


def load_student_module():
    try:
        import main
        return main
    except ImportError:
        assert False, "Could not import main.py. Ensure your file is named main.py."


def test_has_solve_function():
    main = load_student_module()
    assert hasattr(main, "solve"), "Your code must contain a function named 'solve(n: int)'."
    assert callable(main.solve), "solve must be a callable function."


def test_solve_base_cases():
    main = load_student_module()
    assert main.solve(0) == 0, "Failed base case solve(0). Expected 0."
    assert main.solve(1) == 1, "Failed base case solve(1). Expected 1."


def test_solve_standard_cases():
    main = load_student_module()
    assert main.solve(5) == 5, f"Failed solve(5). Expected 5, got {main.solve(5)}"
    assert main.solve(10) == 55, f"Failed solve(10). Expected 55, got {main.solve(10)}"


def test_solve_edge_cases():
    main = load_student_module()
    assert main.solve(-5) == 0, "Failed edge case for negative numbers. Expected 0."
