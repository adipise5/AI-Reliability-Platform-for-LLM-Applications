from __future__ import annotations

from report_generator.domain.entities import ReportFormat
from report_generator.domain.errors import UnsupportedReportFormatError
from report_generator.domain.ports import ReportRenderer


class InMemoryReportRendererRegistry:
    def __init__(self, renderers: list[ReportRenderer]) -> None:
        self._renderers = {renderer.format: renderer for renderer in renderers}

    def get(self, format: ReportFormat) -> ReportRenderer:
        renderer = self._renderers.get(format)
        if renderer is None:
            raise UnsupportedReportFormatError(format.value)
        return renderer
