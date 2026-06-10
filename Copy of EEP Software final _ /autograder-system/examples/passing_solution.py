def solve(n: int) -> int:
    """
    Returns the nth Fibonacci number.
    solve(0) = 0
    solve(1) = 1
    solve(2) = 1
    ...
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
