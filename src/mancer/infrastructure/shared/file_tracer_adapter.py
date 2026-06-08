"""Adapter FileTracer do protokołu FileContentProvider z domain."""

from typing import Optional

from .file_tracer import FileTracer


class FileTracerContentProvider:
    """Implementacja FileContentProvider delegująca do FileTracer (lokalnie lub zdalnie)."""

    def __init__(self, tracer: FileTracer, is_remote: bool = False):
        self._tracer = tracer
        self._is_remote = is_remote

    def get_content(self, path: str) -> str:
        return self._tracer._get_file_content(path, self._is_remote)

    def set_content(self, path: str, content: str) -> bool:
        return self._tracer._set_file_content(path, content, self._is_remote)

    def backup_file(self, path: str, suffix: Optional[str] = None) -> Optional[str]:
        try:
            return self._tracer.backup_file(path, self._is_remote, suffix)
        except Exception:
            return None
