# 基于深度学习的网络入侵检测系统 — 设计文档

> 日期：2026-06-08 | 类型：毕业设计 | 目标用户：学术/学位评审

## 1. 项目概述

一个完整的网络入侵检测系统（NIDS），使用多模态 Transformer 进行流量分类，支持已知攻击识别和未知攻击检测，并提供 Web 可视化界面用于实时监控与答辩演示。

### 核心技术路线

- **模型架构**：双编码器 Late Fusion + Transformer + OpenMax（未知攻击检测）
- **数据处理**：统计特征（CICFlowMeter）+ 原始载荷（Scapy 字节序列）双模态
- **系统交付**：PyTorch 模型 + FastAPI 后端 + React 前端 + 完整的 Web 演示系统
- **可解释性**：SHAP 特征重要性 + Transformer 注意力权重可视化

---

## 2. 系统架构

六层架构设计：

| 层 | 职责 | 关键技术 |
|---|---|---|
| **展示层** | 6 页面 Web UI | React 18 + TypeScript + shadcn/ui |
| **API 网关层** | REST + WebSocket | FastAPI + WebSocket |
| **检测引擎层** | 流量预处理、特征提取、推理编排 | Scapy + CICFlowMeter |
| **模型层** | 多模态 Transformer + OpenMax | PyTorch |
| **数据层** | 检测日志、实验追踪、模型存储 | MySQL 8.0 + MLflow |
| **数据采集层** | pcap 上传、实时抓包、数据集加载 | Scapy |

### 检测数据流

```
pcap/实时抓包 → 流量解析引擎 → 特征提取(双路并行) → 多模态模型推理 → OpenMax 判定 → WebSocket 推送结果
```

---

## 3. 模型架构（Late Fusion）

### 3.1 统计特征分支（Statistical Encoder）

```
输入：CICFlowMeter 80+ 维统计特征
  → VarianceThreshold 特征选择（保留 ≥60 维）
  → StandardScaler 标准化
  → Linear 投影到 d_model=256
  → Transformer Encoder × 4 层（8 heads, FFN=1024, LayerNorm, Dropout=0.1）
  → Global Average Pooling → f_stat (256d)
```

### 3.2 载荷序列分支（Payload Encoder）

```
输入：每流前 20 包 × 128 字节 = 2560 字节序列
  → Byte Embedding（256 维）
  → 位置编码（max_len=1024）
  → Transformer Encoder × 6 层（8 heads, FFN=1024, Pre-LN, Dropout=0.1）
  → [CLS] Token Pooling → f_payload (256d)
```

### 3.3 融合与分类

```
f_stat (256d) ⊕ f_payload (256d)
  → Concat(512d) → Linear → Dropout(0.1) → ReLU → LayerNorm → f_fused (256d)
  → Softmax Head: Linear(256 → K) — 已知攻击分类
  → OpenMax Head: EVT Weibull 分布拟合激活向量 — 未知攻击检测
```

### 3.4 训练配置

| 超参数 | 值 |
|---|---|
| 损失函数 | CrossEntropyLoss + Label Smoothing (ε=0.1) |
| 优化器 | AdamW (lr=1e-4, weight_decay=0.01) |
| 学习率调度 | CosineAnnealingWarmRestarts (T_0=10) |
| Batch Size | 64 |
| Epochs | 100（Early Stopping patience=15） |
| 正则化 | Dropout=0.1, LayerNorm, Weight Decay |

---

## 4. 数据预处理管道

### 阶段 1：原始流量解析
- Scapy 逐包读取 pcap
- 五元组流重组（src_ip + dst_ip + src_port + dst_port + protocol）
- 数据清洗：去 NaN、去重、过滤无效流

### 阶段 2：双路特征提取（并行）

**路径 A — 统计特征：**
CICFlowMeter 提取 → 特征工程（Ratio 特征、时间窗口聚合）→ 特征选择（方差阈值 + 相关性过滤，保留 ≥60 维）→ StandardScaler

**路径 B — 载荷序列：**
Scapy 提取前 20 包载荷（每包 128 字节）→ 截断/填充至 2560 字节固定长度 → Byte Embedding (256d) → LayerNorm

### 阶段 3：数据划分与增强
- 分层划分：60% train / 20% val / 20% test（stratified by attack class）
- 类别平衡：WeightedRandomSampler
- 数据增强：统计特征加 Gaussian Noise，载荷随机丢包模拟
- 预缓存：预处理结果存为 `.pt` 文件

### 支持数据集
- CIC-IDS 2017（15 类攻击）
- CSE-CIC-IDS 2018（14 类攻击）
- UNSW-NB15（9 类攻击）
- 自定义 pcap 上传

---

## 5. 前端页面设计

| 页面 | 路由 | 核心组件 |
|---|---|---|
| **仪表盘** | `/dashboard` | 统计卡片（检测数/告警数/准确率/速率）、24h 趋势图、攻击分布饼图、实时告警时间线、系统状态面板 |
| **实时检测** | `/live` | WebSocket 推送滚动流量表、告警 Toast 弹出、实时速率图、暂停/恢复控制 |
| **流量详情** | `/traffic/:id` | 五元组元信息、检测结论与置信度、注意力热力图、SHAP Top-10 柱状图、载荷 Hex Dump、统计特征完整列表 |
| **可视化大屏** | `/bigscreen` | D3.js 攻击路径拓扑图、世界地图攻击分布（ECharts）、24h 攻击时间线堆叠柱状图、攻击类型 Top 排名、数字滚动 Counter 动画、跑马灯告警条、全屏模式 |
| **历史记录** | `/history` | 筛选搜索表格（IP/端口/攻击类型/日期）、分页、CSV/PDF 导出、删除 |
| **模型管理** | `/model` | 版本信息、混淆矩阵热力图、ROC 曲线、SHAP Summary Plot、MLflow 实验链接 |

### 前端技术栈
- React 18 + TypeScript
- shadcn/ui（组件库）
- Recharts（常规图表）
- D3.js（攻击路径拓扑）
- ECharts（世界地图）
- WebSocket 客户端（实时推送）

---

## 6. API 设计

### 统一响应格式

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": { "page": 1, "limit": 50, "total": 342 }
}
```

### 端点清单

#### 检测相关
| 方法 | 端点 | 说明 |
|---|---|---|
| POST | `/api/detect/pcap` | 上传 pcap 文件，异步检测，返回 task_id |
| GET | `/api/detect/task/{task_id}` | 查询检测任务进度与结果 |
| POST | `/api/detect/single` | 单条流量实时检测（输入流特征 JSON） |
| WS | `/ws/live` | WebSocket 实时检测推送 |

#### 历史记录
| 方法 | 端点 | 说明 |
|---|---|---|
| GET | `/api/alerts` | 告警列表（分页、筛选、排序） |
| GET | `/api/alerts/{id}` | 单条告警详情（含 SHAP + 注意力数据） |
| DELETE | `/api/alerts/{id}` | 删除告警 |
| GET | `/api/alerts/export?format=csv\|pdf` | 导出告警报告 |

#### 模型管理
| 方法 | 端点 | 说明 |
|---|---|---|
| GET | `/api/model/info` | 当前模型版本、参数量、指标 |
| GET | `/api/model/metrics` | 混淆矩阵、ROC 数据 |
| POST | `/api/model/reload` | 热加载新模型权重 |

#### 系统
| 方法 | 端点 | 说明 |
|---|---|---|
| GET | `/api/system/status` | 运行状态、网卡信息、运行时长 |
| GET | `/api/system/stats` | 仪表盘统计数据 |

### WebSocket 消息格式

```json
{
  "type": "detection_result",
  "timestamp": "2026-06-08T14:32:15Z",
  "flow_id": "uuid",
  "src_ip": "172.16.0.5",
  "dst_ip": "10.0.0.7",
  "protocol": "HTTP",
  "prediction": "BruteForce",
  "confidence": 0.946,
  "is_unknown": false,
  "top_features": [{"name": "flow_duration", "importance": 0.32}]
}
```

---

## 7. 数据库设计（MySQL 8.0）

### detection_logs

```sql
CREATE TABLE detection_logs (
    id            CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    src_ip        VARCHAR(45) NOT NULL,
    dst_ip        VARCHAR(45) NOT NULL,
    src_port      INT,
    dst_port      INT,
    protocol      VARCHAR(10) NOT NULL,
    prediction    VARCHAR(50) NOT NULL,
    confidence    FLOAT NOT NULL,
    is_unknown    TINYINT(1) DEFAULT 0,
    is_attack     TINYINT(1) DEFAULT 0,
    stat_features JSON,
    payload_hash  VARCHAR(64),
    shap_data     JSON,
    attn_data     JSON,
    source        VARCHAR(20) DEFAULT 'pcap',
    model_version VARCHAR(20),
    INDEX idx_created_at (created_at DESC),
    INDEX idx_prediction (prediction),
    INDEX idx_src_ip (src_ip),
    INDEX idx_is_attack (is_attack)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### model_versions

```sql
CREATE TABLE model_versions (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    version       VARCHAR(20) NOT NULL UNIQUE,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_path     TEXT NOT NULL,
    metrics       JSON NOT NULL,
    params_count  INT,
    is_active     TINYINT(1) DEFAULT 0
);
```

### experiments

```sql
CREATE TABLE experiments (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    run_name      VARCHAR(100) NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    hyperparams   JSON,
    metrics       JSON,
    artifacts_path TEXT
);
```

---

## 8. 错误处理

### 分层错误处理

| 层级 | 策略 |
|---|---|
| **前端** | Error Boundary 捕获渲染崩溃；API 统一 try/catch + toast；WebSocket 指数退避重连（1s→2s→4s→8s→max 30s） |
| **API 层** | FastAPI 全局 Exception Handler；Pydantic 校验 → 422；模型未加载 → 503；文件格式错误 → 400 |
| **检测引擎** | 预处理失败 → 跳过该条流并计数；推理异常 → 退回 Softmax 阈值法；EVT 拟合失败 → 退回 Softmax 阈值法 |
| **模型层** | CUDA OOM → 自动切 CPU；权重加载失败 → 拒绝启动并报错 |

### 关键边界场景

| 场景 | 处理 |
|---|---|
| pcap 过大 (>2GB) | 前端限制 + 后端分块流式解析 + 进度条 |
| 模型未加载时请求 | 503 + "模型加载中，预计还需 X 秒" |
| WebSocket 断连 | 服务端缓存最近 200 条，重连后补推 |
| 检测速率不足 | 采样丢弃（保留告警优先）+ 显示丢弃率 |
| MySQL 写入失败 | 本地 SQLite 兜底缓存 + 定时批量重试 |

---

## 9. 测试策略

### 测试金字塔

| 类型 | 占比 | 工具 | 目标 |
|---|---|---|---|
| 单元测试 | 50% | pytest + pytest-cov | 特征提取、模型组件、API 工具函数 |
| 集成测试 | 30% | pytest + FastAPI TestClient | API 端点、数据库 CRUD、预处理管道、模型推理端到端 |
| E2E 测试 | 20% | Playwright | 6 页面加载、pcap 上传检测、WebSocket、大屏 |

### 关键测试文件

```
tests/
├── unit/
│   ├── test_preprocessing.py
│   ├── test_model_stat_encoder.py
│   ├── test_model_payload_encoder.py
│   ├── test_fusion.py
│   ├── test_openmax.py
│   └── test_metrics.py
├── integration/
│   ├── test_api_detect.py
│   ├── test_ws_live.py
│   ├── test_pipeline_e2e.py
│   └── test_db_crud.py
└── e2e/
    ├── test_dashboard_loads.spec.ts
    ├── test_live_detection.spec.ts
    ├── test_upload_and_detect.spec.ts
    └── test_bigscreen.spec.ts
```

### 模型评估目标

| 指标 | 目标 |
|---|---|
| 已知攻击 F1-Score (macro) | ≥ 0.92 |
| 已知攻击 F1-Score (per class) | ≥ 0.85（每类） |
| 未知攻击检出率 (OpenMax) | ≥ 0.75 — 测试集中未知类样本被正确标记为 Unknown 的比例 |
| 推理延迟 | < 5ms/流 (GPU) / < 50ms/流 (CPU) |

---

## 10. 技术栈总览

| 层 | 选型 | 版本 |
|---|---|---|
| 深度学习框架 | PyTorch | ≥ 2.0 |
| 后端 | FastAPI | ≥ 0.110 |
| 前端 | React + TypeScript | 18 + 5.x |
| UI 组件 | shadcn/ui | latest |
| 可视化 | Recharts + D3.js + ECharts | latest |
| 数据库 | MySQL | 8.0 |
| ORM | SQLAlchemy (async) | 2.0 |
| 异步驱动 | aiomysql | latest |
| 流量解析 | Scapy + CICFlowMeter | latest |
| 实验管理 | MLflow | ≥ 2.0 |
| 可解释性 | SHAP | latest |
| E2E 测试 | Playwright | latest |
| 单元测试 | pytest + pytest-cov | latest |

---

## 11. 项目结构（规划）

```
nids/
├── backend/
│   ├── api/                # FastAPI 路由
│   ├── core/               # 配置、异常处理
│   ├── models/             # PyTorch 模型定义
│   │   ├── stat_encoder.py
│   │   ├── payload_encoder.py
│   │   ├── fusion.py
│   │   └── openmax.py
│   ├── engine/             # 检测引擎
│   │   ├── preprocessor.py
│   │   ├── feature_extractor.py
│   │   └── detector.py
│   ├── db/                 # 数据库模型与操作
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── pages/          # 6 页面
│   │   ├── components/     # 共享组件
│   │   ├── hooks/          # 自定义 hooks
│   │   └── lib/            # API 客户端、工具函数
│   └── e2e/
├── data/                   # 数据集与预处理缓存
├── experiments/            # MLflow 实验记录
├── notebooks/              # Jupyter 实验笔记
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-06-08-nids-design.md
```
