"""Domain extraction for confirmed Markdown reports."""
import json
import logging
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.config import settings

logger = logging.getLogger(__name__)


DOMAINS = {"技术", "金融", "医疗", "教育", "政策", "产品", "其他"}


class MetadataExtractor:
    """Extract minimal document metadata for Milvus scalar filtering."""

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
                ("system", "你负责给中文研究报告分类。只输出 JSON，不要解释。domain 必须是：技术、金融、医疗、教育、政策、产品、其他 之一。"),
                ("human", "标题：{title}\n\n正文片段：{preview}\n\n请输出：{{\"domain\":\"...\"}}"),
            ])
            self.chain = prompt | self.llm
        return self.chain

    def _heuristic_domain(self, text: str) -> str:
        rules = [
            ("技术", r"AI|人工智能|模型|算法|软件|系统|RAG|Agent|数据库|架构|工程|编程|芯片|云计算"),
            ("金融", r"金融|银行|证券|基金|股票|债券|保险|利率|货币|投资|融资"),
            ("医疗", r"医疗|医院|药物|临床|疾病|健康|诊断|治疗|医保"),
            ("教育", r"教育|学校|课程|教学|学生|教师|考试|学习"),
            ("政策", r"政策|法规|监管|政府|法律|标准|条例|合规"),
            ("产品", r"产品|用户|市场|竞品|需求|商业化|增长|运营"),
        ]
        for domain, pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                return domain
        return "其他"

    def extract_domain(self, title: str, content: str) -> str:
        text = f"{title}\n{content[:2000]}"
        fallback = self._heuristic_domain(text)
        try:
            raw = self._get_chain().invoke({"title": title, "preview": content[:2000]}).content
            data = json.loads(raw)
            domain = str(data.get("domain", "")).strip()
            if domain in DOMAINS:
                return domain
            logger.warning("Invalid extracted domain=%s, fallback=%s", domain, fallback)
        except Exception:
            logger.exception("Domain extraction failed, fallback=%s", fallback)
        return fallback
