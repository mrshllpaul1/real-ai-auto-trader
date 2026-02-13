from types import SimpleNamespace

from conftest import should_skip_backend_tests


def test_should_skip_backend_tests_when_url_missing():
    module = SimpleNamespace(BASE_URL="")
    assert should_skip_backend_tests(module)


def test_should_skip_backend_tests_when_url_missing_scheme():
    module = SimpleNamespace(BASE_URL="localhost:8001")
    assert should_skip_backend_tests(module)


def test_should_skip_backend_tests_when_url_valid():
    module = SimpleNamespace(BASE_URL="http://localhost:8001")
    assert not should_skip_backend_tests(module)


def test_should_not_skip_backend_tests_without_base_url_attr():
    module = SimpleNamespace()
    assert not should_skip_backend_tests(module)
