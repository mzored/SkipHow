from runner import ready_names


def test_ready_jobs_keep_priority_order() -> None:
    assert ready_names([(1, "invoice"), (2, "email"), (3, "cleanup")]) == [
        "invoice",
        "email",
        "cleanup",
    ]
