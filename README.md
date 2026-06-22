# AI-NIDS

<div align="center">

**Network Intrusion Detection System** — 基于深度学习的网络入侵检测系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c)](https://pytorch.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

> **声明**：本项目是学习使用 AI 辅助开发过程中的产物，主要用于技术学习和实践探索，仅供参考。如有不足之处，欢迎指正。

## 概述

AI-NIDS 是一个基于**多模态 Transformer** 的入侵检测系统，能够对网络流量进行实时分类，识别已知攻击类型，并利用 **OpenMax** 算法检测未知攻击。

### 核心特性

- **多模态融合** — 同时分析 80 维统计特征和原始 Payload 字节序列
- **开集识别** — OpenMax 算法检测未知/零日攻击
- **实时检测** — WebSocket 推送实时检测结果
- **可视化大屏** — D3.js 拓扑图 + 攻击时间线
- **可解释 AI** — SHAP 值 + 注意力热力图分析检测原因
- **模型管理** — 版本管理、混淆矩阵、ROC 曲线

## 架构

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│         React 18 + TypeScript + Vite             │
│         Recharts / D3.js / ECharts               │
└──────────────────┬──────────────────────────────┘
                   │ REST / WebSocket
┌──────────────────▼──────────────────────────────┐
│            Backend (FastAPI)                     │
│   Detection Engine  ───  API Routers            │
│   PyTorch Inference ───  SQLAlchemy Async       │
└──────┬─────────────────────────────┬────────────┘
       │                             │
┌──────▼──────┐           ┌─────────▼─────────┐
│   MySQL     │           │   Model Store     │
│  Detection  │           │  (Checkpoints)    │
│   Logs      │           │                   │
└─────────────┘           └───────────────────┘
```

### 模型架构

| 组件 | 说明 |
|------|------|
| **StatEncoder** | Transformer 编码 80 维统计流特征 |
| **PayloadEncoder** | Transformer 编码 Payload 字节序列 (vocab 256, max_len 2560) |
| **LateFusionClassifier** | 拼接 [CLS] 嵌入 → MLP → 分类 |
| **OpenMax** | Weibull 分布重校准，拒绝未知样本 |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0

### 1. 克隆项目

```bash
git clone https://github.com/qtk233/AI_NIDS.git
cd AI_NIDS
```

### 2. 创建虚拟环境 & 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（根据终端选择）
venv\Scripts\activate          # Windows PowerShell / CMD
# source venv/Scripts/activate # Windows (Git Bash)
# source venv/bin/activate     # Linux / macOS

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
# 导入建库建表脚本
mysql -u root -p < init_db.sql
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 中的 DATABASE_URL，替换用户名和密码
```

### 5. 训练模型（可选）

```bash
python train.py \
  --stat processed/train_stat.pt \
  --payload processed/train_payload.pt \
  --labels processed/train_labels.pt \
  --val-stat processed/val_stat.pt \
  --val-payload processed/val_payload.pt \
  --val-labels processed/val_labels.pt \
  --epochs 100 \
  --batch-size 64
```

训练完成后，模型权重保存在 `checkpoints/best.pt`。

### 6. 启动后端

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

API 文档访问：http://localhost:8000/docs

### 7. 启动前端

```bash
cd frontend
npm install
npm run dev -- --open
```

## 测试

```bash
# 运行所有后端测试
pytest backend/tests/ -v

# 运行测试并生成覆盖率报告
pytest backend/tests/ -v --cov=backend --cov-report=term-missing

# 运行前端 E2E 测试（需先启动后端和前端）
cd frontend
npx playwright test
```

## 项目结构

```
.
├── backend/                  # FastAPI + PyTorch 后端
│   ├── main.py               # FastAPI 入口 (CORS, routers, exception handlers)
│   ├── core/                 # 配置、数据库、异常
│   ├── models/               # PyTorch 模型组件
│   ├── engine/               # 检测引擎 (流量解析、特征提取、检测器)
│   ├── api/                  # REST API + WebSocket
│   ├── db/                   # SQLAlchemy ORM + CRUD
│   ├── schemas/              # Pydantic 请求/响应模型
│   ├── training/             # 数据集、训练循环、评估指标
│   └── tests/                # 单元测试 + 集成测试
├── frontend/                 # React 18 + TypeScript + Tailwind CSS 4 + Vite
│   └── src/
│       ├── pages/            # 6 个页面组件
│       ├── components/       # Layout, StatCard, FlowTable
│       ├── hooks/            # useApi, useWebSocket
│       └── lib/              # API 客户端、类型定义
├── data/                     # 原始数据集
├── processed/                # 预处理缓存 (.pt)
├── checkpoints/              # 模型权重
├── notebooks/                # Jupyter notebooks
├── train.py                  # 训练入口 (argparse + MLflow)
├── preprocess.py             # 数据预处理脚本
├── init_db.sql               # MySQL 建表脚本
├── requirements.txt          # Python 依赖
├── .env.example              # 环境变量模板
├── CLAUDE.md                 # AI 辅助开发配置
└── README.md                 # 本文件
```

## 页面

| 路由 | 页面 | 功能 |
|------|------|------|
| `/dashboard` | 仪表盘 | 统计卡片、趋势图 (Recharts)、攻击分布 |
| `/live` | 实时检测 | WebSocket 实时推送检测结果 |
| `/traffic/:id` | 流量详情 | 元信息、SHAP 解释、注意力热力图 |
| `/bigscreen` | 可视化大屏 | D3.js 拓扑图 + 攻击时间线 |
| `/history` | 历史记录 | 告警搜索/筛选/分页/导出 |
| `/model` | 模型管理 | 版本信息、混淆矩阵、ROC 曲线 |

## API 设计

所有端点使用统一响应格式: `{success: boolean, data: T | null, error: string | null, meta?: {...}}`

| 路由 | 端点 | 说明 |
|------|------|------|
| `system` | `/api/system/stats`, `/api/system/health` | 系统状态、健康检查 |
| `detect` | `/api/detect/pcap` (POST multipart) | 上传 PCAP 进行检测 |
| `alerts` | `/api/alerts`, `/api/alerts/{id}` | 分页告警 CRUD |
| `model` | `/api/model/info`, `/api/model/metrics` | 模型版本与评估指标 |
| `ws` | `/ws/detections` | WebSocket 实时检测推送 |

## 技术栈

| 层 | 技术 |
|---|---|
| 深度学习 | PyTorch 2.0+, Transformer, OpenMax |
| 后端 | FastAPI, WebSocket, SQLAlchemy Async |
| 前端 | React 18, TypeScript, Tailwind CSS, Vite |
| 可视化 | Recharts, D3.js, ECharts |
| 数据库 | MySQL 8.0 |
| 流量处理 | Scapy |
