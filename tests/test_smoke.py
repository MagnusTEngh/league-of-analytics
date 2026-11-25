"""Smoke tests for the league_of_analytics package."""


def test_package_imports():
    import league_of_analytics

    assert league_of_analytics.__doc__ is not None
