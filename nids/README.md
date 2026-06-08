# NIDS — Network Intrusion Detection System

基于深度学习的网络入侵检测系统，使用多模态 Transformer 进行流量分类，支持已知攻击识别和未知攻击检测。

## 技术栈

| 层 | 技术 |
|---|---|
| 深度学习 | PyTorch 2.0+, Transformer Encoder |
| 后端 | FastAPI + WebSocket |
| 前端 | React 18 + TypeScript + Tailwind CSS |
| 数据库 | MySQL 8.0 (SQLAlchemy async) |
| 可视化 | Recharts + D3.js + ECharts |
| 流量处理 | Scapy + CICFlowMeter |

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- MySQL 8.0

### 后端启动

```bash
cd backend
cp .env.example .env  # 编辑数据库连接
source ../venv/Scripts/activate  # Windows
# source ../venv/bin/activate    # Linux/Mac
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

## 项目结构

```
nids/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── core/                # 配置、数据库、异常
│   ├── models/              # PyTorch 模型 (StatEncoder, PayloadEncoder, Fusion, OpenMax)
│   ├── engine/              # 检测引擎 (流量解析、特征提取、检测器)
│   ├── api/                 # REST API + WebSocket
│   ├── db/                  # SQLAlchemy ORM + CRUD
│   ├── schemas/             # Pydantic 请求/响应模型
│   └── training/            # 数据集、训练循环、评估指标
├── frontend/
│   └── src/
│       ├── pages/           # 6 个页面
│       ├── components/      # 共享组件
│       ├── hooks/           # 自定义 hooks
│       └── lib/             # API 客户端、类型定义
├── data/                    # 原始数据集
├── processed/               # 预处理缓存 (.pt)
└── checkpoints/             # 模型权重
```

## 页面

| 路由 | 页面 | 功能 |
|---|---|---|
| `/dashboard` | 仪表盘 | 统计卡片、趋势图、攻击分布 |
| `/live` | 实时检测 | WebSocket 实时推送流量检测结果 |
| `/traffic/:id` | 流量详情 | 元信息、SHAP、注意力热力图 |
| `/bigscreen` | 可视化大屏 | D3.js 拓扑图、攻击时间线 |
| `/history` | 历史记录 | 告警搜索、筛选、导出 |
| `/model` | 模型管理 | 版本信息、混淆矩阵、ROC |
