# Ticket Grabber Suite v2.0

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **免责声明**：本项目仅供技术学习与研究使用，**严禁用于商业用途或黄牛囤票行为**。使用本工具产生的任何后果由使用者自行承担。

## 项目介绍

**Ticket Grabber Suite** 是一个开源的跨平台抢票自动化工具套件，提供精美的 Web 管理界面，支持大麦网、猫眼、12306 等多个票务平台的自动化抢票。

## v2.0 更新内容

- **性能优化**：引擎基类重构，统一 `safe_click` / `screenshot` / `wait_for_navigation` 等通用方法，消除三大引擎间的重复代码
- **智能重试**：可配置最大重试次数、重试间隔，失败后自动重新尝试
- **数据持久化**：任务数据 JSON 自动保存，服务重启不丢失
- **反检测增强**：浏览器指纹伪装、随机延迟、WebDriver 属性隐藏
- **12306 专用字段**：出发站、到达站、车次号、席别独立字段，不再复用 session/price
- **并发控制**：智能控制同时运行的任务数，避免资源耗尽
- **全新前端**：统一 Zustand 数据流，消除多处独立轮询；搜索/筛选/批量操作；分步创建向导
- **系统监控**：CPU、内存、运行时间实时展示
- **批量操作**：支持批量开始、停止、删除任务

## 功能特性

| 特性 | 说明 |
|------|------|
| 多平台支持 | 大麦网、猫眼电影、12306 铁路 |
| 精美 Web 界面 | React + Tailwind CSS 深色主题管理面板 |
| 定时抢票 | 设定开抢时间，自动卡点执行 |
| 智能重试 | 失败自动重试，可配置次数和间隔 |
| 实时日志 | SSE 实时推送，掌握抢票全过程 |
| 反检测 | 浏览器指纹伪装、随机延迟、WebDriver 隐藏 |
| 数据持久化 | JSON 自动保存，重启不丢失 |
| 批量操作 | 批量开始、停止、删除任务 |
| 并发控制 | 智能控制同时运行任务数 |
| 系统监控 | CPU、内存、运行时间实时展示 |

## 技术架构

```
┌─────────────────────────────────────────┐
│            React Frontend                │
│   Dashboard / Tasks / Settings          │
│      Tailwind + Zustand + Lucide        │
├─────────────────────────────────────────┤
│            FastAPI Backend               │
│      REST API + SSE Log Stream          │
├─────────────────────────────────────────┤
│    Task Manager + JSON Persistence      │
│      Retry / Concurrency Control        │
├─────────────────────────────────────────┤
│   Playwright Engines (Damai/Maoyan/     │
│        12306) + Anti-Detection          │
└─────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+（仅开发时需要）
- Chrome/Chromium 浏览器

### 1. 克隆项目

```bash
git clone https://github.com/520llw/ticket-grabber-suite.git
cd ticket-grabber-suite
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

### 3. 启动服务

```bash
python main.py
```

前端已预构建，启动后端后直接访问 **http://localhost:8000** 即可使用完整系统。

### 4. 开发模式（可选）

如需修改前端代码：

```bash
cd frontend
pnpm install
pnpm run dev
```

前端开发服务器运行在 http://localhost:5173，自动代理 API 到后端。

## 使用指南

### 创建抢票任务

1. 点击"新建任务"按钮
2. **第 1 步**：选择平台（大麦 / 猫眼 / 12306）
3. **第 2 步**：填写任务信息
   - **大麦/猫眼**：任务名称、演出链接、日期、场次、票档、数量、观演人
   - **12306**：任务名称、出发站、到达站、日期、车次号、席别、乘车人
4. **第 3 步**：高级设置（定时、重试次数、重试间隔、优先级、无头模式等）
5. 点击"创建任务"

### 启动抢票

1. 在任务列表或详情页点击"开始抢票"
2. 首次使用需在浏览器窗口中**手动完成登录**（扫码或账号密码）
3. 登录后脚本自动执行抢票流程
4. 如设置了定时，脚本会等待到目标时间再开始

### 各平台配置

| 平台 | 必填字段 | 可选字段 |
|------|---------|---------|
| 大麦 | 演出链接 | 日期、场次、票档、数量、观演人 |
| 猫眼 | 演出链接 | 日期、场次、票档、数量、观演人 |
| 12306 | 出发站、到达站、日期 | 车次号、席别、乘车人 |

## API 文档

启动后访问 http://localhost:8000/api/docs 查看 Swagger 文档。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tasks` | 获取任务列表（支持筛选） |
| POST | `/api/tasks` | 创建任务 |
| PUT | `/api/tasks/{id}` | 更新任务 |
| DELETE | `/api/tasks/{id}` | 删除任务 |
| POST | `/api/tasks/{id}/start` | 启动抢票 |
| POST | `/api/tasks/{id}/stop` | 停止抢票 |
| POST | `/api/tasks/{id}/restart` | 重启任务 |
| GET | `/api/tasks/{id}/logs` | 获取日志 |
| GET | `/api/tasks/{id}/logs/stream` | SSE 实时日志 |
| POST | `/api/tasks/batch/start` | 批量启动 |
| POST | `/api/tasks/batch/stop` | 批量停止 |
| POST | `/api/tasks/batch/delete` | 批量删除 |
| GET | `/api/status` | 系统状态 |
| GET | `/api/platforms` | 平台信息 |

## 项目结构

```
ticket-grabber-suite/
├── backend/
│   ├── api/routes.py         # FastAPI 路由
│   ├── core/manager.py       # 任务管理器（持久化、重试、并发）
│   ├── core/models.py        # 数据模型（含12306专用字段）
│   ├── engines/base.py       # 引擎基类（反检测、通用操作）
│   ├── engines/damai.py      # 大麦网引擎
│   ├── engines/maoyan.py     # 猫眼引擎
│   ├── engines/train.py      # 12306引擎
│   ├── config/settings.py    # 全局配置
│   ├── main.py               # 服务入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # UI 组件
│   │   ├── pages/            # 页面
│   │   ├── services/api.ts   # API 服务
│   │   └── store/useStore.ts # Zustand 状态管理
│   ├── dist/                 # 预构建产物
│   └── package.json
├── README.md
├── SPEC.md
└── LEGAL_NOTICE.md
```

## 注意事项

1. **登录方式**：非 headless 模式下会打开浏览器窗口，需手动完成登录
2. **抢票成功率**：本工具模拟人工操作，不保证 100% 成功
3. **反检测**：已内置反检测措施，但无法完全规避平台风控
4. **道德使用**：请通过官方渠道购票，支持正版，抵制黄牛

## 开发计划

- [x] 大麦网抢票引擎
- [x] 猫眼抢票引擎
- [x] 12306 抢票引擎
- [x] Web 管理界面
- [x] 智能重试机制
- [x] 数据持久化
- [x] 批量操作
- [x] 并发控制
- [ ] 验证码自动识别
- [ ] 微信/邮件通知推送
- [ ] Docker 一键部署
- [ ] 多账号并发抢票

## 贡献

欢迎提交 Issue 和 Pull Request！

## License

[MIT License](LICENSE)
