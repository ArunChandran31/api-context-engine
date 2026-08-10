import time

import pytest

from app.utils.timing import Timer


def test_timer_measures_elapsed_time() -> None:
    timer = Timer()

    timer.start()
    time.sleep(0.01)
    elapsed_ms = timer.stop()

    assert elapsed_ms >= 0
    assert timer.elapsed_ms == elapsed_ms


def test_timer_requires_start_before_stop() -> None:
    timer = Timer()

    with pytest.raises(RuntimeError, match="Timer has not been started"):
        timer.stop()


def test_timer_requires_stop_before_reading_elapsed_time() -> None:
    timer = Timer()

    timer.start()

    with pytest.raises(RuntimeError, match="Timer has not been stopped"):
        _ = timer.elapsed_ms


def test_timer_can_be_restarted() -> None:
    timer = Timer()

    timer.start()
    first_elapsed = timer.stop()

    timer.start()
    second_elapsed = timer.stop()

    assert first_elapsed >= 0
    assert second_elapsed >= 0
