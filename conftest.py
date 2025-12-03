# Root conftest.py - controls test collection
# Only legacy tests are currently active. New test suites (unit, integration, e2e)
# are under development and explicitly excluded from collection.

collect_ignore_glob = [
    "tests/unit/*",
    "tests/integration/*",
    "tests/e2e/*",
    "prototypes/*",
    "tools/*",
]

