from __future__ import annotations

import logging
import random
import time

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Rate limiter
class RateLimiter:
    def __init__(self, min_interval_seconds: float = 0.2):
        self.min_interval = min_interval_seconds
        self.last_call: float = 0.0

    def wait(self):
        elapsed = time.monotonic() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.monotonic()

# Backoff with jitter
def backoff_with_jitter(attempt: int, base: float = 0.5, cap: float = 30.0) -> float:
    """
        Returns a sleep duration in seconds for the given retry attempt (0-indexed).
    """
    exp = min(cap, base * (2 ** attempt))
    return  random.uniform(0, exp)

# Circuit breaker    
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitOpenError(Exception):
    """
        Raised when a request is rejected because the circuit is open.
    """

@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    cooldown_seconds: float = 60.0

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    failure_count: int = field(default=0, init=False)
    opened_at: float = field(default=0.0, init=False)

    @property
    def state(self) -> CircuitState:
        # Lazily transition OPEN -> HALF_OPEN once the cooldown has elapsed
        if self._state is CircuitState.OPEN:
            if time.monotonic() - self.opened_at >= self.cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: OPEN -> HALF_OPEN (cooldown elapsed)")
        return self._state

    def before_call(self) -> None:
        if self._state is CircuitState.OPEN:
            raise CircuitOpenError(
                f"Circuit is OPEN; rejecting call without hitting the network "
                f"(retry after {self.cooldown_seconds}s cooldown)."
            )

    def on_success(self) -> None:
        if self._state is CircuitState.HALF_OPEN:
            logger.info("Circuit breaker: HALF_OPEN -> CLOSED (trial call successful)")
        self._state = CircuitState.CLOSED
        self.failure_count = 0

    def on_failure(self) -> None:
        if self._state is CircuitState.HALF_OPEN:
            # trial call failed -> back to OPEN immediately, reset cooldown
            logger.warning("Circuit breaker: HALF_OPEN -> OPEN (trial call failed)")
            self._state = CircuitState.OPEN
            self.opened_at = time.monotonic()
            return

        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            logger.warning(
                "Circuit breaker: CLOSED -> OPEN (%d consecutive failures)",
                self.failure_count
            )
            self._state = CircuitState.OPEN
            self.opened_at = time.monotonic()

# Client that wires all three together
class ResilientOpenMeteoClient:
    def __init__(
            self, min_interval_seconds: float = 0.2,
            max_retries: int = 3,
            failure_threshold: int = 5,
            cooldown_seconds: float = 60.0,
            timeout: float = 10.0):
        self.rate_limiter = RateLimiter(min_interval_seconds)
        self.breaker = CircuitBreaker(failure_threshold, cooldown_seconds)
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()

    def get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
            Fetch JSON from `url`. Raises CircuitOpenError immediately (no network
            call) if the breaker is open. Raises the last exception if all retries
            within a single call are exhausted without tripping the breaker.
        """

        self.breaker.before_call()

        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            self.rate_limiter.wait()
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                self.breaker.on_success()
                return resp.json()

            except (requests.exceptions.RequestException) as e:
                last_exc = e
                logger.warning(
                    "Request failed (attempt %d/%d): %s", attempt + 1, self.max_retries, e
                )
                if attempt < self.max_retries - 1:
                    time.sleep(backoff_with_jitter(attempt))

        self.breaker.on_failure()
        assert last_exc is not None
        raise last_exc

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = ResilientOpenMeteoClient()
    data = client.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": 52.52, "longitude": 13.41, "hourly": "temperature_2m"}
    )
    print(list(data.keys()))