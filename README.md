# 自动化深度研究智能体系统

TODO 驱动的全自动深度研究助手，使用 LangChain + FastAPI + Vue 3 构建。

## 功能特点

- **三 Agent 协作架构**: 规划 → 搜索 → 总结 → 报告自动生成
- **实时进度推送**: 通过 SSE 推送实时进度到前端
- **多种搜索引擎**: 支持 Tavily（推荐）和 DuckDuckGo（免费无密钥）
- **流式报告生成**: 最终报告支持流式输出，逐步显示
- **中文优化**: 所有 Agent Prompt 和输出都是中文

## 项目结构

```
research_agent/
├── backend/
│   ├── main.py                  # FastAPI 入口
│   ├── agents/
│   │   ├── planner.py           # TODO 规划 Agent
│   │   ├── summarizer.py        # 任务总结 Agent
│   │   └── reporter.py          # 报告撰写 Agent
│   ├── services/
│   │   ├── planning_service.py
│   │   ├── search_service.py
│   │   ├── summarization_service.py
│   │   └── reporting_service.py
│   ├── tools/
│   │   └── search_tool.py       # 搜索工具封装
│   ├── schemas.py               # Pydantic 数据模型
│   └── config.py                # 配置
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── components/
│   │   │   ├── SearchBox.vue
│   │   │   ├── ResearchModal.vue
│   │   │   ├── TodoList.vue
│   │   │   └── ReportViewer.vue
│   │   └── composables/
│   │       └── useResearch.ts   # SSE 逻辑封装
│   └── package.json
├── .env.example
└── requirements.txt
```

## 架构说明

### 三个 Agent 协作

1. **TODO Planner**: 将用户研究主题分解为 3~5 个子任务，输出 JSON
2. **Task Summarizer**: 接收单个子任务的搜索结果，生成结构化摘要（JSON）
3. **Report Writer**: 整合所有摘要，流式输出最终 Markdown 报告

## 环境准备

### 1. 创建 Conda 环境

```bash
conda create -n research python=3.10
conda activate research
```

### 2. 安装后端依赖

```bash
cd research_agent
pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 配置环境变量

创建 `.env` 文件并填写你的 API Key:

编辑 `.env`:

```env
# LLM 
填写你的llm信息
LLM_API_KEY = xxx
LLM_MODEL_ID = xxx
LLM_BASE_URL = xxx

# 搜索 - 推荐使用 Tavily
TAVILY_API_KEY=your_tavily_api_key_here
SEARCH_ENGINE=tavily

# 如果没有 Tavily API Key，可以用 DuckDuckGo（免费但有限制）
# SEARCH_ENGINE=duckduckgo
```

> 获取 Tavily API Key: https://tavily.com/

## 启动服务

### 1. 启动后端

```bash
cd research_agent/backend
python main.py
```

后端将在 `http://localhost:8000` 启动。

### 2. 启动前端（另开终端）

```bash
cd research_agent/frontend
npm run dev
```

前端将在 `http://localhost:5173` 启动，打开浏览器访问即可使用。

## 使用流程

1. 在首页输入你的研究主题（例如：`LangChain 框架最新发展趋势`）
2. 点击「开始研究」
3. 在弹出窗口中查看实时进度：
   - 首先 AI 会制定研究计划（分解为子任务）
   - 然后逐个对子任务进行搜索和总结
   - 最后生成完整的 Markdown 报告
4. 研究完成后，可以查看完整报告


## 技术栈

- **后端**: Python 3.10+, LangChain, FastAPI
- **前端**: Vue 3, TypeScript, Vite, marked.js
- **搜索引擎**: Tavily / DuckDuckGo
- **LLM**: doubaoSeed（推荐，也兼容其他 OpenAI 格式模型）
