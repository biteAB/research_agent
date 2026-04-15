"""Storage and confirmation flow for generated Markdown reports."""
import asyncio
import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from backend.config import settings
from backend.rag.indexer import RagIndexer

logger = logging.getLogger(__name__)


class PendingReport(BaseModel):
    report_id: str
    topic: str
    pending_path: str
    metadata_path: str


class ConfirmIndexResult(BaseModel):
    report_id: str
    knowledge_path: str
    indexed_chunks: int


class ReportStorageService:
    """Save generated reports and index them only after user confirmation."""

    def __init__(self):
        self.pending_dir = Path(settings.PENDING_REPORT_DIR)
        self.knowledge_dir = Path(settings.KNOWLEDGE_BASE_DIR)
        self.indexer: RagIndexer | None = None

    def _get_indexer(self) -> RagIndexer:
        if self.indexer is None:
            self.indexer = RagIndexer()
        return self.indexer

    def _safe_name(self, value: str) -> str:
        value = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", value).strip("_")
        return value[:48] or "research_report"

    def _unique_path(self, directory: Path, stem: str, suffix: str) -> Path:
        path = directory / f"{stem}{suffix}"
        if not path.exists():
            return path

        index = 2
        while True:
            candidate = directory / f"{stem}_{index}{suffix}"
            if not candidate.exists():
                return candidate
            index += 1

    def _report_file_stem(self, topic: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{self._safe_name(topic)}"

    async def save_pending_report(self, report_id: str, topic: str, markdown: str) -> PendingReport:
        self.pending_dir.mkdir(parents=True, exist_ok=True)

        file_stem = self._report_file_stem(topic)
        md_path = self._unique_path(self.pending_dir, file_stem, ".md")
        meta_path = self.pending_dir / f"{report_id}.json"

        logger.info("Saving pending report: report_id=%s path=%s", report_id, md_path)
        md_path.write_text(markdown, encoding="utf-8")

        payload = {
            "report_id": report_id,
            "topic": topic,
            "pending_path": str(md_path),
            "file_stem": md_path.stem,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "indexed": False,
        }
        meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        return PendingReport(
            report_id=report_id,
            topic=topic,
            pending_path=str(md_path),
            metadata_path=str(meta_path),
        )

    def get_pending_report(self, report_id: str) -> PendingReport:
        meta_path = self.pending_dir / f"{report_id}.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Pending report metadata not found: {report_id}")

        data = json.loads(meta_path.read_text(encoding="utf-8"))
        return PendingReport(
            report_id=data["report_id"],
            topic=data["topic"],
            pending_path=data["pending_path"],
            metadata_path=str(meta_path),
        )

    async def confirm_and_index_report(self, report_id: str) -> ConfirmIndexResult:
        report = self.get_pending_report(report_id)
        meta_path = Path(report.metadata_path)
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        if data.get("indexed") and data.get("knowledge_path"):
            knowledge_path = Path(data["knowledge_path"])
            if knowledge_path.exists():
                logger.info("Report already indexed, reusing existing knowledge file: %s", knowledge_path)
                return ConfirmIndexResult(
                    report_id=report_id,
                    knowledge_path=str(knowledge_path),
                    indexed_chunks=int(data.get("indexed_chunks") or 0),
                )

        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        source_path = Path(report.pending_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Pending report markdown not found: {source_path}")

        target_stem = data.get("file_stem") or source_path.stem or self._report_file_stem(report.topic)
        target_path = self._unique_path(self.knowledge_dir, target_stem, ".md")

        logger.info("Confirming report into knowledge base: report_id=%s target=%s", report_id, target_path)
        shutil.copyfile(source_path, target_path)

        index_result = await asyncio.to_thread(
            self._get_indexer().index_file,
            target_path,
            report_id,
        )

        data["indexed"] = True
        data["knowledge_path"] = str(target_path)
        data["indexed_chunks"] = index_result["indexed_chunks"]
        data["indexed_at"] = datetime.now().isoformat(timespec="seconds")
        meta_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        return ConfirmIndexResult(
            report_id=report_id,
            knowledge_path=str(target_path),
            indexed_chunks=index_result["indexed_chunks"],
        )


_report_storage_service_instance: ReportStorageService | None = None


def get_report_storage_service() -> ReportStorageService:
    global _report_storage_service_instance
    if _report_storage_service_instance is None:
        _report_storage_service_instance = ReportStorageService()
    return _report_storage_service_instance
