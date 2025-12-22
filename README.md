# 上市公司深度研究 Agent 系统

基于 AI Agent 的上市公司深度研究系统，能够自动收集、分析上市公司信息并生成专业的研究报告。

## 技术栈

- **前端**: Vue 3 + Vite + TypeScript + Element Plus
- **后端**: Python + FastAPI + Agno Framework
- **搜索工具**: Google Serper API
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **报告生成**: PDF 导出 (ReportLab)

## 功能特性

- 🔍 智能数据收集 - 使用 Serper API 搜索公司信息
- 📊 财务深度分析 - 盈利能力、偿债能力、运营效率、成长性分析
- 📈 市场地位分析 - 行业分析、竞争格局、SWOT 分析
- 📄 专业报告生成 - 结构化研究报告 + PDF 导出
- ⚡ 实时进度推送 - WebSocket 实时进度更新

## 快速开始

### 1. 环境要求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) - Python 包管理器
- Node.js 18+
- pnpm 或 npm

### 2. 配置环境变量

在 `backend` 目录下创建 `.env` 文件：

```bash
# LLM Configuration (OpenAI Compatible)
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# Serper API
SERPER_API_KEY=your_serper_api_key

# Database
DATABASE_URL=sqlite+aiosqlite:///./research.db
```

### 3. 启动后端

```bash
cd backend

# 使用 uv 同步依赖并创建虚拟环境
uv sync

# 启动服务
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 5. 访问应用

打开浏览器访问 http://localhost:5173

## 项目结构

```
company-research-agent/
├── frontend/                    # Vue 前端
│   ├── src/
│   │   ├── components/         # Vue 组件
│   │   ├── views/              # 页面视图
│   │   ├── api/                # API 调用
│   │   ├── stores/             # Pinia 状态管理
│   │   └── types/              # TypeScript 类型
│   └── package.json
│
├── backend/                     # Python 后端
│   ├── app/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   ├── models/             # 数据模型
│   │   ├── api/                # API 路由
│   │   ├── agents/             # Agno Agent 实现
│   │   ├── tools/              # Agent 工具
│   │   └── services/           # 业务服务
│   └── requirements.txt
│
├── env.example.txt             # 环境变量示例
└── README.md
```

## Agent 架构

系统采用多 Agent 协同架构：

1. **ResearchOrchestrator** - 主协调 Agent，负责分解任务和协调其他 Agent
2. **DataCollectorAgent** - 数据收集 Agent，使用 Serper 搜索公司信息
3. **FinancialAnalyzerAgent** - 财务分析 Agent，分析财务报表和指标
4. **MarketAnalyzerAgent** - 市场分析 Agent，分析行业地位和竞争格局
5. **ReportGeneratorAgent** - 报告生成 Agent，整合分析结果生成报告

## API 接口

### 研究相关

- `POST /api/research/start` - 启动研究任务
- `GET /api/research/{task_id}/status` - 获取任务状态
- `GET /api/research/{task_id}/result` - 获取研究结果
- `GET /api/research/history` - 获取历史记录
- `WebSocket /api/research/{task_id}/progress` - 实时进度推送

### 报告相关

- `GET /api/reports` - 获取报告列表
- `GET /api/reports/{report_id}` - 获取报告详情
- `GET /api/reports/{report_id}/pdf` - 下载 PDF 报告
- `POST /api/reports/{task_id}/generate` - 从任务生成报告

## 使用说明

1. 在首页输入公司名称或股票代码
2. 选择研究深度（基础/标准/深度）
3. 可选择关注重点领域
4. 点击"开始研究"启动 AI 研究流程
5. 实时查看研究进度
6. 研究完成后查看报告并可下载 PDF

## 注意事项

- Serper API 有调用限制，请合理使用
- 研究结果基于公开信息，仅供参考
- 投资有风险，请谨慎决策

## License

MIT

