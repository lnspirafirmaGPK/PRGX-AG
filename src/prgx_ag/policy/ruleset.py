BLOCKED_PATTERNS: dict[str, str] = {
    'delete_core': 'Attempt to delete core systems is prohibited.',
    'shutdown_nexus': 'Unauthorized shutdown operation is prohibited.',
    'exploit': 'Exploit behavior is prohibited.',
    'destructive recursion': 'Destructive recursion pattern is prohibited.',
    'infinite loop': 'Unsafe infinite loop behavior is prohibited.',
    'mass deletion': 'Mass deletion behavior is prohibited.',
}

PRINCIPLES: list[str] = ['Non-Harm', 'Efficiency', 'Truthfulness', 'Transparency', 'No Infinite Loops']
