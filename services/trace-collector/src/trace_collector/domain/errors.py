from __future__ import annotations


class TraceCollectorError(Exception):
    """Base class for all domain errors raised by the Trace Collector."""


class TraceNotFoundError(TraceCollectorError):
    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id
        super().__init__(f"no trace {trace_id!r} has been ingested")


class EmptyBatchError(TraceCollectorError):
    def __init__(self) -> None:
        super().__init__("span ingestion requires at least one span")
