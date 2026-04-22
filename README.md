# Ticket Grabber Suite 🎫

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> ⚠️ **免责声明**：本项目仅供技术学习与研究使用，**严禁用于商业用途或黄牛囤票行为**。使用本工具产生的任何后果由使用者自行承担。

## 项目介绍

**Ticket Grabber Suite** 是一个开源的跨平台抢票自动化工具套件，提供精美的 Web 管理界面，支持大麦网、猫眼、12306 等多个票务平台的自动化抢票。

本项目参考并整合了以下开源项目的设计理念：
- [MakiNaruto/Automatic_ticket_purchase](https://github.com/MakiNaruto/Automatic_ticket_purchase) — 大麦抢票参考
- [testerSunshine/12306](https://github.com/testerSunshine/12306) — 12306抢票参考
- [pjialin/py12306](https://github.com/pjialin/py12306) — Web管理界面参考

## 功能特性

- 🎭 **多平台支持**：大麦网、猫眼电影、12306铁路，可扩展自定义平台
- 🖥️ **精美Web界面**：React + Tailwind CSS 深色主题管理面板
- ⏰ **定时抢票**：支持设定开抢时间，自动卡点执行
- 📊 **实时监控**：任务状态、实时日志流、系统状态面板
- 🚀 **浏览器自动化**：基于 Playwright，模拟真实用户操作
- 📝 **可视化配置**：无需编写代码，表单化创建抢票任务
- 🔔 **即时通知**：抢票成功/失败实时推送日志

## 技术架构

```
┌─────────────────────────────────────────┐
│            React Frontend                │
│   (Dashboard / Tasks / Settings)        │
│         Tailwind + Framer Motion         │
├─────────────────────────────────────────┤
│            FastAPI Backend               │
│      (REST API + SSE Log Stream)        │
├─────────────────────────────────────────┤
│        Task Manager + Scheduler         │
├─────────────────────────────────────────┤
│   Playwright Engines (Damai/Maoyan/     │
│            12306/Custom)                │
└─────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
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

### 3. 启动后端服务

```bash
python -m uvicorn main:app --reload --port 8000
```

### 4. 安装并启动前端

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器默认运行在 http://localhost:5173

### 5. 访问管理界面

打开浏览器访问 http://localhost:5173 即可使用管理面板。

## 使用指南

### 创建抢票任务

1. 点击"新建任务"按钮
2. **步骤1**：填写任务名称，选择平台（大麦/猫眼/12306），粘贴演出/车票页面URL
3. **步骤2**：配置抢票参数：日期、场次、票档价格、购票数量、观演人/乘车人
4. **步骤3**（可选）：设置定时开抢时间，是否使用headless模式
5. 点击"创建任务"

### 启动抢票

1. 在任务列表或详情页点击"开始抢票"按钮
2. 如果是首次使用，系统会打开浏览器窗口，请**手动完成登录**（扫码或输入账号密码）
3. 登录完成后，脚本会自动执行后续抢票流程
4. 如果设置了定时，脚本会等待到目标时间再开始

### 查看实时日志

进入任务详情页，可以：
- 查看历史日志
- 通过 SSE 实时接收抢票过程日志
- 不同级别日志有不同颜色标识

## 各平台配置说明

| 平台 | URL示例 | date | session | price | buyers |
|------|---------|------|---------|-------|--------|
| 大麦 | `https://detail.damai.cn/...` | 演出日期 | 场次时间 | 票档价格如"580" | 观演人姓名 |
| 猫眼 | `https://www.maoyan.com/...` | 演出日期 | 场次时间 | 票档价格 | 观演人姓名 |
| 12306 | `https://kyfw.12306.cn/...` | 乘车日期 | 出发站-到达站如"北京南-上海虹桥" | 席别如"二等座" | 乘车人姓名 |

## 项目结构

```
ticket-grabber-suite/
├── backend/
│   ├── api/              # FastAPI 路由
│   ├── core/             # 任务管理器、数据模型
│   ├── engines/          # 抢票引擎（大麦/猫眼/12306）
│   ├── config/           # 全局配置
│   ├── main.py           # 服务入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # UI 组件
│   │   ├── pages/        # 页面
│   │   ├── services/     # API 服务
│   │   └── store/        # 状态管理
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── SPEC.md               # 项目规范文档
├── LEGAL_NOTICE.md       # 免责声明
└── README.md             # 本文件
```

## 注意事项

1. **登录方式**：非 headless 模式下会打开真实浏览器窗口，需要用户手动完成登录（大麦/猫眼扫码，12306账号密码）
2. **抢票成功率**：本工具仅模拟人工操作，**不保证100%抢票成功**，成功率取决于网络速度、电脑性能和平台反爬策略
3. **反检测**：工具已内置基本的反检测措施（随机延迟、隐藏 webdriver 属性等），但无法完全规避平台的风控
4. **道德使用**：请通过官方渠道购票，支持正版，抵制黄牛

## API 文档

启动后端后访问 http://localhost:8000/docs 查看自动生成的 Swagger API 文档。

主要接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tasks` | 获取所有任务 |
| POST | `/api/tasks` | 创建任务 |
| POST | `/api/tasks/{id}/start` | 启动抢票 |
| POST | `/api/tasks/{id}/stop` | 停止抢票 |
| GET | `/api/tasks/{id}/logs` | 获取日志 |
| GET | `/api/tasks/{id}/logs/stream` | SSE 实时日志流 |
| GET | `/api/status` | 系统状态 |

## 开发计划

- [x] 大麦网抢票引擎
- [x] 猫眼抢票引擎
- [x] 12306抢票引擎
- [x] Web管理界面
- [ ] 验证码自动识别集成
- [ ] 多账号并发抢票
- [ ] 微信/邮件通知推送
- [ ] Docker 一键部署
- [ ] 分布式抢票集群

## 贡献

欢迎提交 Issue 和 Pull Request！

## License

[MIT License](LICENSE)

---

> 🎫 祝你抢票成功，观演愉快！
