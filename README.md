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
conda create -n deepresearch python=3.10
conda activate deepresearch
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

复制 `.env.example` 到 `.env` 并填写你的 API Key:

```bash
cp .env.example .env
```

编辑 `.env`:

```env
# LLM - 需要 OpenAI API Key（或兼容 OpenAI 格式的接口）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_NAME=gpt-4o
# 如果使用第三方代理，设置 BASE URL
# OPENAI_BASE_URL=https://api.openai.com/v1

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

## API 接口

- `POST /api/research/start` - 开始研究，返回 `{ task_id: uuid }`
- `GET /api/research/stream/{task_id}` - SSE 实时进度推送

## SSE 事件类型

| 事件类型       | 说明                 |
|----------------|----------------------|
| `planning`     | 规划完成，返回 TODO 列表 |
| `searching`    | 正在搜索某个子任务 |
| `summarizing`  | 正在总结某个子任务 |
| `summary_done` | 子任务总结完成 |
| `reporting`    | 开始生成报告 |
| `report_chunk` | 报告流式片段 |
| `done`         | 全部完成 |
| `error`        | 出错信息 |

## 技术栈

- **后端**: Python 3.10+, LangChain, FastAPI, asyncio
- **前端**: Vue 3, TypeScript, Vite, marked.js
- **搜索引擎**: Tavily / DuckDuckGo
- **LLM**: OpenAI GPT-4o（推荐，也兼容其他 OpenAI 格式模型）

## 注意事项

- 如果使用 DuckDuckGo，请不要频繁请求，否则会被限流
- 推荐使用 Tavily，搜索结果质量更高，专门为 AI 搜索设计
- 所有 LLM 调用都是异步的，支持并发搜索
- 搜索结果有缓存，重复查询会直接使用缓存结果
