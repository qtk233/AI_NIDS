# AI-NIDS

<div align="center">

**Network Intrusion Detection System** — 基于深度学习的网络入侵检测系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c)](https://pytorch.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

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

## 模型架构

| 组件 | 说明 |
|------|------|
| **StatEncoder** | Transformer 编码 80 维统计流特征 |
| **PayloadEncoder** | Transformer 编码 Payload 字节序列 |
| **LateFusionClassifier** | 拼接 [CLS] 嵌入 → MLP → 分类 |
| **OpenMax** | Weibull 分布重校准，拒绝未知样本 |

## 快速入门

```bash
# 后端
cd nids
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload

# 前端（新终端）
cd nids/frontend
npm install
npm run dev
```

详细文档请参阅 [`nids/README.md`](nids/README.md)。

## 项目结构

```
AI-NIDS/
├── nids/
│   ├── backend/           # FastAPI + PyTorch
│   ├── frontend/          # React + TypeScript
│   ├── data/              # 原始数据集
│   ├── processed/         # 预处理缓存
│   ├── checkpoints/       # 模型权重
│   ├── train.py           # 训练入口
│   └── init_db.sql        # 数据库初始化
├── CLAUDE.md              # AI 辅助开发配置
└── README.md              # 本文件
```

## 技术栈

| 层 | 技术 |
|---|---|
| 深度学习 | PyTorch 2.0+, Transformer, OpenMax |
| 后端 | FastAPI, WebSocket, SQLAlchemy Async |
| 前端 | React 18, TypeScript, Tailwind CSS, Vite |
| 可视化 | Recharts, D3.js, ECharts |
| 数据库 | MySQL 8.0 |
| 流量处理 | Scapy |
