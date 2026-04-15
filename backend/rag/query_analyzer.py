"""Query rewrite and metadata filter analysis."""
import json
import logging
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.config import settings
from backend.rag.metadata_extractor import DOMAINS
from backend.rag.schemas import QueryAnalysis

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Produce query rewrite, expansions and Milvus filter expressions."""

    REFERENCE_RE = re.compile(r"(参考|引用|来源|链接|出处|citation|reference|source)", re.IGNORECASE)

    def __init__(self):
        self.llm: ChatOpenAI | None = None
        self.chain = None

    def _get_chain(self):
        if self.chain is None:
            self.llm = ChatOpenAI(
                api_key=settings.get_effective_api_key(),
                model=settings.get_effective_model(),
                base_url=settings.get_effective_base_url(),
                temperature=0,
            )
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你负责将用户问题改写为适合检索本地知识库的查询。只输出 JSON。domain 只能是 技术、金融、医疗、教育、政策、产品、其他 或 null。expanded_queries 输出 0-2 个。"),
                ("human", "用户问题：{question}\n输出格式：{{\"rewritten_query\":\"...\",\"expanded_queries\":[\"...\"],\"domain\":null,\"include_references\":false}}"),
            ])
            self.chain = prompt | self.llm
        return self.chain

    def _heuristic_domain(self, question: str) -> str | None:
        for domain in DOMAINS - {"其他"}:
            if domain in question:
                return domain
        return None

    def _escape_value(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _build_filter_expr(self, domain: str | None, include_references: bool, doc_id: str | None) -> str:
        chunk_types = ["title", "section", "reference"] if include_references else ["title", "section"]
        expr = f'chunk_type in {chunk_types}'
        if domain and domain in DOMAINS and domain != "其他":
            expr += f' and domain == "{domain}"'
        if doc_id:
            expr += f' and doc_id == "{self._escape_value(doc_id)}"'
        return expr

    def analyze(
        self,
        question: str,
        *,
        doc_id: str | None = None,
        domain: str | None = None,
        include_references: bool | None = None,
    ) -> QueryAnalysis:
        heuristic_include_refs = bool(self.REFERENCE_RE.search(question))
        if include_references is not None:
            include_refs = include_references
        else:
            include_refs = heuristic_include_refs
        selected_domain = domain if domain in DOMAINS else self._heuristic_domain(question)
        rewritten = question
        expanded: list[str] = []

        if settings.ENABLE_QUERY_REWRITE:
            try:
                raw = self._get_chain().invoke({"question": question}).content
                data = json.loads(raw)
                rewritten = str(data.get("rewritten_query") or question).strip()
                expanded = [str(item).strip() for item in data.get("expanded_queries", []) if str(item).strip()][:2]
                candidate_domain = data.get("domain")
                if selected_domain is None and candidate_domain in DOMAINS and candidate_domain != "其他":
                    selected_domain = candidate_domain
                if include_references is None:
                    include_refs = bool(data.get("include_references", include_refs)) or include_refs
            except Exception:
                logger.exception("Query analysis failed, using heuristic query analysis")

        filter_expr = self._build_filter_expr(selected_domain, include_refs, doc_id)
        return QueryAnalysis(
            original_query=question,
            rewritten_query=rewritten,
            expanded_queries=expanded,
            domain=selected_domain,
            include_references=include_refs,
            filter_expr=filter_expr,
        )
