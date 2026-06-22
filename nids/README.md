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

### 1. 克隆项目 & 进入目录

```bash
git clone <repo-url>
cd nids
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

**检查 MySQL 服务状态：**

```powershell
Get-Service -Name MySQL*
```

若 `Status` 为 `Stopped`，启动服务：

```powershell
Start-Service -Name MySQL80   # 服务名视版本而定：MySQL80 / MySQL57 / MySQL
```

服务启动后，导入建库建表脚本：

```powershell
# PowerShell
Get-Content init_db.sql | mysql -u root -p

# Git Bash / Linux / macOS
mysql -u root -p < init_db.sql
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 中的 DATABASE_URL，替换用户名和密码
```

### 5. 准备训练数据（可选）

将原始流量数据放入 `data/` 目录，运行预处理脚本生成 `.pt` 文件到 `processed/` 目录。

### 6. 训练模型（可选）

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

### 7. 启动后端

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

API 文档访问：http://localhost:8000/docs

### 8. 启动前端

```bash
cd frontend
npm install
npm run dev -- --open
```

Vite 默认不会自动打开浏览器，`--open` 参数让其自动打开。若端口 5173 被占用，Vite 会自动尝试下一个端口（如 5174），终端输出以实际显示的地址为准。

### 9. 运行测试

```bash
# 运行所有后端测试
pytest backend/tests/ -v

# 运行测试并生成覆盖率报告
pytest backend/tests/ -v --cov=backend --cov-report=term-missing

# 运行单个测试文件
pytest backend/tests/unit/test_openmax.py -v

# 运行前端 E2E 测试（需先启动后端和前端）
cd frontend
npx playwright test
```

## 日常开发（PowerShell）

首次配置完成后，日常启动项目的 PowerShell 操作流程：

```powershell
# 1. 进入项目目录
cd nids

# 2. 激活虚拟环境
venv\Scripts\activate

# 3. 检查 MySQL 服务状态，若未运行则启动
Get-Service -Name MySQL*
# 如果 Status 为 Stopped，启动服务（服务名视版本而定）：
Start-Service -Name MySQL80

# 4. 启动后端（API 文档 http://localhost:8000/docs）
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 5. 新开一个 PowerShell 窗口，启动前端
cd nids/frontend
npm run dev -- --open    # 自动打开浏览器；若端口被占用会自动换端口
```

> **注意**：`uvicorn` 命令的 `backend.main:app` 路径基于 `nids/` 目录。不要在 `nids/frontend/` 下执行此命令，否则会报 `ModuleNotFoundError: No module named 'backend'`。

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
