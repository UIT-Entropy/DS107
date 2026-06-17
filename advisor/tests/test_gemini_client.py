from advisor.gemini.client import is_retryable_generation_error


class FakeApiError(Exception):
    status_code = 503


def test_retryable_generation_error_detects_503():
    assert is_retryable_generation_error(FakeApiError("high demand"))


def test_retryable_generation_error_detects_rate_limit_message():
    assert is_retryable_generation_error(Exception("429 rate limit"))


def test_retryable_generation_error_detects_ssl_eof_message():
    assert is_retryable_generation_error(
        Exception("[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol")
    )


def test_retryable_generation_error_ignores_other_errors():
    assert not is_retryable_generation_error(ValueError("bad request"))
