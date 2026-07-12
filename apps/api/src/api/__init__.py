"""The FastAPI application layer.

Thin by design: it owns HTTP, auth, tenancy resolution, and run lifecycle
endpoints, then delegates all real work to the orchestration core. No business
logic lives here — the API translates requests into orchestration calls and
orchestration results into responses.
"""

__all__: list[str] = []
