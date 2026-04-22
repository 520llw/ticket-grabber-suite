# SPEC.md — Ticket Grabber Suite 项目规范

## 1. 项目概述
跨平台抢票自动化工具套件，提供Web管理界面，支持大麦网、猫眼、12306等票务平台的自动化抢票。

## 2. 技术栈
- **后端**: Python 3.10+, FastAPI, Playwright, Pydantic, asyncio
- **前端**: React 18, Tailwind CSS, shadcn/ui, Axios
- **部署**: 本地运行，浏览器自动化驱动

## 3. 目录结构
```
ticket-bot/
├── backend/
│   ├── api/              # FastAPI路由
│   ├── core/             # 任务管理器、调度器
│   ├── engines/          # 抢票引擎（大麦、猫眼、12306）
│   ├── utils/            # 工具函数
│   ├── config/           # 配置管理
│   └── main.py           # 服务入口
├── frontend/
│   ├── src/
│   │   ├── components/   # UI组件
│   │   ├── pages/        # 页面
│   │   ├── services/     # API服务
│   │   └── store/        # 状态管理
│   └── index.html
├── docs/                 # 文档
├── README.md
└── requirements.txt
```

## 4. 后端架构

### 4.1 数据模型
```python
class TaskConfig(BaseModel):
    id: str
    name: str                    # 任务名称
    platform: Literal["damai", "maoyan", "12306", "custom"]
    url: str                     # 目标页面URL
    date: str                    # 目标日期
    session: str                 # 场次
    price: str                   # 票档价格
    ticket_count: int = 1        # 购票数量
    buyers: list[str]           # 观演人/乘车人
    cron_time: Optional[str]   # 定时开抢时间
    status: Literal["idle", "running", "success", "failed", "stopped"]
    created_at: datetime
    updated_at: datetime

class TaskLog(BaseModel):
    task_id: str
    timestamp: datetime
    level: Literal["info", "warn", "error", "success"]
    message: str
```

### 4.2 抢票引擎接口
```python
class BaseEngine(ABC):
    @abstractmethod
    async def login(self, context): ...
    @abstractmethod
    async def grab(self, task: TaskConfig) -> bool: ...
    @abstractmethod
    async def check_stock(self, task: TaskConfig) -> bool: ...
```

### 4.3 API路由
- `GET /api/tasks` — 获取所有任务
- `POST /api/tasks` — 创建任务
- `PUT /api/tasks/{id}` — 更新任务
- `DELETE /api/tasks/{id}` — 删除任务
- `POST /api/tasks/{id}/start` — 启动抢票
- `POST /api/tasks/{id}/stop` — 停止抢票
- `GET /api/tasks/{id}/logs` — 获取任务日志（SSE流）
- `GET /api/status` — 系统状态

### 4.4 核心流程
1. 用户通过前端配置任务参数
2. 任务管理器将任务加入队列
3. 到达抢票时间时启动Playwright浏览器实例
4. 引擎执行登录→选座→下单流程
5. 实时推送日志到前端
6. 抢票成功/失败时更新状态并发送通知

## 5. 前端架构

### 5.1 页面结构
- `/` — 仪表盘（任务概览、运行状态）
- `/tasks` — 任务管理列表
- `/tasks/new` — 创建新任务（分步骤表单）
- `/tasks/:id` — 任务详情（日志实时流）
- `/settings` — 全局设置

### 5.2 组件清单
- `Layout` — 侧边栏+主内容区布局
- `TaskCard` — 任务卡片（状态、平台、倒计时）
- `TaskForm` — 多步骤任务配置表单
- `LogViewer` — 实时日志流组件（SSE接收）
- `StatusBadge` — 状态徽章
- `CountdownTimer` — 开抢倒计时
- `PlatformSelector` — 平台选择器（带图标）

### 5.3 设计风格
- 深色主题（#0f172a 背景）
- 主色调：emerald/teal 绿色系（成功/抢票主题）
- 卡片式布局，圆角xl
- 实时数据用脉冲动画
- 抢票中状态用流光效果

## 6. 引擎实现规范

### 6.1 大麦引擎 (DamaiEngine)
- 基于Playwright，headless=False（需要用户扫码/登录）
- 流程：登录页→商品页→选择日期场次→选择票档→确认观演人→提交订单
- 防检测：随机延迟、真实鼠标轨迹（可选）
- 支持定时刷新，到点自动点击

### 6.2 猫眼引擎 (MaoyanEngine)
- 类似大麦，适配猫眼页面DOM结构
- 支持微信小程序跳转（如需要）

### 6.3 12306引擎 (Train12306Engine)
- 参考testerSunshine/12306设计
- 支持候补抢票
- 验证码处理（打码平台接口预留）

## 7. 安全与免责声明
- 代码中必须包含免责声明：仅供学习研究，禁止商业用途/黄牛行为
- 用户需自行承担使用风险
- 模拟人工操作，不保证100%成功
