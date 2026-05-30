import json
import logging

from de_lakehouse_pipeline.logging_utils import JsonLogFormatter


def test_json_log_formatter_includes_extra_fields() -> None:
    record = logging.LogRecord(
        name="de_lakehouse_pipeline.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="pipeline step finished",
        args=(),
        exc_info=None,
    )
    record.step_name = "build_marts"
    record.row_count = 3

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "de_lakehouse_pipeline.test"
    assert payload["message"] == "pipeline step finished"
    assert payload["step_name"] == "build_marts"
    assert payload["row_count"] == 3
