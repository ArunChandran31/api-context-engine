from time import perf_counter


class Timer:
    """
    Measure elapsed wall-clock time with high-resolution timing.
    """

    def __init__(self) -> None:
        self._start: float | None = None
        self._elapsed_ms: float | None = None

    def start(self) -> None:
        """Start the timer."""
        self._start = perf_counter()
        self._elapsed_ms = None

    def stop(self) -> float:
        """
        Stop the timer and return elapsed time in milliseconds.
        """
        if self._start is None:
            raise RuntimeError("Timer has not been started.")

        self._elapsed_ms = (perf_counter() - self._start) * 1000
        return self._elapsed_ms

    @property
    def elapsed_ms(self) -> float:
        """
        Return the measured elapsed time in milliseconds.
        """
        if self._elapsed_ms is None:
            raise RuntimeError("Timer has not been stopped.")

        return self._elapsed_ms
