# CourseFlow - 分布式 AI 课程生成系统

基于 gRPC + Redis 的多 Agent 协作平台，支持任务队列持久化、状态同步和失败重试机制

## 🎯 项目简介

CourseFlow 是一个分布式 AI 课程生成系统，通过多个 AI Agent 协作完成课程的调研、大纲制定、章节编写和全文审核。系统采用微服务架构，使用 Redis 作为任务队列和状态存储，gRPC 实现服务间通信，确保高可靠性和可扩展性。

## ✨ 核心特性

- 🔥 多 Agent 协作：研究、写作、审核、润色等多个专业 Agent 协同工作
- 📦 Redis 任务队列：任务持久化存储，支持高并发
- 🔒 分布式锁：防止任务重复执行，确保数据一致性
- 🔄 失败重试机制：指数退避算法，自动重试失败任务
- 💓 心跳保活：防止 Worker 宕机导致任务锁死
- 🌐 gRPC 通信：高效的跨服务通信和状态同步
- 📊 实时状态追踪：任务状态实时更新，支持监控和查询

##  🚀 快速开始

环境要求

- Python >= 3.11
- Redis Server
- gRPC 支持

安装依赖

`pip install -r requirements.txt`

配置环境变量

```
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

.env 示例：

```yml
# AI API Key
DASHSCOPE_API_KEY=your-dashscope-api-key

# 可选：搜索 API
SERPER_API_KEY=your-serper-api-key

# Redis 配置（默认即可）
REDIS_HOST=localhost
REDIS_PORT=6379
```

启动服务

1️⃣ 启动 Worker（服务端）

```
python main.py
```

2️⃣ 提交任务（客户端）

```
python produce_task.py
```

交互式输入课程主题和要求，系统将自动完成课程生成。

执行示例：

```
==================================================
AI Course Generation Client (Interactive)
AI 课程生成客户端 (交互式)
==================================================

请输入课程主题 (Topic): Python 异步编程
请输入课程要求 (Requirements): 适合初学者

------------------------------
Phase 1: Research (市场调研)
------------------------------
[Task] Submitting 'research' task...
[Wait] Waiting for result... Done! (3.2s)

 建议的课程方向:
1. asyncio 基础概念
2. 实际应用场景
...

请输入您选择的方向: asyncio 基础概念

------------------------------
Phase 2: Outline (大纲制定)
------------------------------
...

🎉 课程生成流程全部完成！

```



### ⚙️ 配置说明

```python
# Redis 配置
# utils/redis_client.py
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# 重试策略
# extend/retry_manager.py
max_retries = 3  # 最大重试次数
backoff_factor = 2  # 退避因子（指数增长）

# gRC配置
# extend/grpc_client.py
GRPC_TARGET = os.getenv('GRPC_TARGET', 'localhost:50051')
```



## 📁 项目结构


```
project5_2/
├── main.py                  # Worker 入口
├── produce_task.py          # Producer 客户端
├── requirements.txt         # Python 依赖
├── .env.example            # 环境变量示例
├── src/
│   ├── course_system.py    # 核心系统逻辑,负责任务编排 (获取 -> 加锁 -> 执行 -> 上报)。
│   ├── protos/             # gRPC proto 文件
│   │   ├── task.proto
│   │   ├── task_pb2.py
│   │   └── task_pb2_grpc.py
│   └── utils/
│       └── redis_client.py # Redis 客户端
├── extend/					# 封装了 Redis、gRPC、重试等通用分布式能力。
│   ├── task_processor.py   # 任务处理器
│   ├── agent_executor.py   # Agent 执行器
│   ├── grpc_client.py      # gRPC 客户端
│   ├── retry_manager.py    # 重试管理器
│   ── state_synchronizer.py # 状态同步器
└── config/                 # 配置文件

```



## 🏗️ 系统架构

```mermaid
graph TB
    subgraph Client["👤 客户端 (Producer)"]
        User["用户输入"]
        Producer["produce_task.py<br/>任务提交客户端"]
    end

    subgraph Redis["📦 Redis 中间件"]
        Queue["任务队列<br/>tasks:default"]
        ProcessingQueue["处理队列<br/>tasks:processing:{worker_id}"]
        StateStore["状态存储<br/>task:{id}:state"]
        Lock["分布式锁<br/>task:{id}:lock"]
    end

    subgraph Worker[" Worker 服务端 (Consumer)"]
        Main["main.py<br/>Worker 入口"]
        CourseSystem["CourseSystem<br/>任务编排器"]
        TaskProcessor["TaskProcessor<br/>任务获取"]
        StateSync["StateSynchronizer<br/>状态同步+锁"]
        RetryManager["RetryManager<br/>重试管理"]
        AgentExecutor["CourseAgentExecutor<br/>AI Agent 执行"]
    end

    subgraph Agents["🤖 AI Agents"]
        Research["🔍 Research Agent<br/>市场调研"]
        Outline["📝 Outline Agent<br/>大纲制定"]
        Chapter["✏️ Chapter Agent<br/>章节编写"]
        Review["✅ Review Agent<br/>全文审核"]
    end

    subgraph Communication["🌐 通信层"]
        GrpcServer["gRPC Server"]
        GrpcClient["gRPC Client"]
        ResultReport["结果回传"]
    end

    %% 数据流
    User --> Producer
    Producer -->|推送任务| Queue
    Queue -->|RPOPLPUSH| ProcessingQueue
    ProcessingQueue --> TaskProcessor
    TaskProcessor --> CourseSystem
    
    CourseSystem -->|加锁| Lock
    CourseSystem -->|更新状态| StateStore
    CourseSystem --> RetryManager
    RetryManager --> AgentExecutor
    
    AgentExecutor --> Research
    AgentExecutor --> Outline
    AgentExecutor --> Chapter
    AgentExecutor 
```



## 📋 工作流程

任务阶段

1. 🔍 Research（市场调研）
   1. 搜索相关主题信息
   2. 提供建议的课程方向
   3. 用户选择方向
2. 📝 Outline（大纲制定）
   1. 生成课程章节结构
   2. 用户确认或修改
3. Chapter Writing（章节编写）
   1. 逐章编写详细内容
   2. 支持修改重写
4. ✅ Review（全文审核）
   1. 质量检查和优化建议
   2. 生成最终课程文档

执行示例：

```
==================================================
AI Course Generation Client (Interactive)
AI 课程生成客户端 (交互式)
==================================================

请输入课程主题 (Topic): Python 异步编程
请输入课程要求 (Requirements): 适合初学者

------------------------------
Phase 1: Research (市场调研)
------------------------------
[Task] Submitting 'research' task...
[Wait] Waiting for result... Done! (3.2s)

 建议的课程方向:
1. asyncio 基础概念
2. 实际应用场景
...

请输入您选择的方向: asyncio 基础概念

------------------------------
Phase 2: Outline (大纲制定)
------------------------------
...

🎉 课程生成流程全部完成！

```

## 🔄 数据流向

```
用户 → Producer → Redis 队列 → Worker → Agents → gRPC → Producer → 用户
```

```mermaid

sequenceDiagram
    participant U as 用户
    participant P as Producer<br/>(produce_task.py)
    participant R as Redis
    participant W as Worker<br/>(main.py)
    participant A as AI Agents
    participant G as gRPC Server

    U->>P: 输入主题和要求
    P->>R: 推送任务到队列
    P->>P: 轮询检查状态
    
    W->>R: 安全获取任务<br/>(RPOPLPUSH)
    R-->>W: 返回任务数据
    
    W->>R: 获取分布式锁
    W->>R: 更新状态: running
    
    W->>A: 执行 Agent 任务
    A-->>W: 返回执行结果
    
    W->>R: 更新状态: completed
    W->>G: gRPC 上报结果
    G-->>P: 回传结果
    
    P->>P: 解析结果
    P-->>U: 展示结果
    
    W->>R: 释放锁
    W->>R: ACK 确认<br/>(从队列移除)
```



## 🔄 运行流程图

```mermaid

flowchart TD
    Start([用户提交任务]) --> Input[输入课程主题和要求]
    Input --> Phase1[Phase 1: Research 调研]
    
    Phase1 --> P1_Submit[提交调研任务到 Redis]
    P1_Submit --> P1_Wait[轮询等待结果]
    P1_Wait --> P1_Check{任务完成?}
    P1_Check -->|否| P1_Wait
    P1_Check -->|是| P1_Result[获取调研结果]
    P1_Result --> P1_Show[展示建议方向]
    P1_Show --> P1_Choose[用户选择方向]
    
    P1_Choose --> Phase2[Phase 2: Outline 大纲]
    Phase2 --> P2_Submit[提交大纲任务到 Redis]
    P2_Submit --> P2_Wait[轮询等待结果]
    P2_Wait --> P2_Check{任务完成?}
    P2_Check -->|否| P2_Wait
    P2_Check -->|是| P2_Result[获取大纲数据]
    P2_Result --> P2_Show[展示章节结构]
    P2_Show --> P2_Decide{用户选择}
    
    P2_Decide -->|确认继续| Phase3
    P2_Decide -->|修改重试| P2_Modify[修改要求]
    P2_Modify --> P2_Submit
    P2_Decide -->|退出| End([结束])
    
    Phase3[Phase 3: Chapter Writing 章节编写]
    P2_Decide -->|确认| P3_Loop[循环处理每一章]
    P3_Loop --> P3_Chapter[处理第 i 章]
    P3_Chapter --> P3_Submit[提交章节任务到 Redis]
    P3_Submit --> P3_Wait[轮询等待结果]
    P3_Wait --> P3_Check{任务完成?}
    P3_Check -->|否| P3_Wait
    P3_Check -->|是| P3_Result[获取章节内容]
    P3_Result --> P3_Show[展示内容预览]
    P3_Show --> P3_Decide{用户选择}
    
    P3_Decide -->|确认本章| P3_Next{还有章节?}
    P3_Decide -->|修改重写| P3_Modify[修改建议]
    P3_Modify --> P3_Submit
    P3_Decide -->|退出| End
    
    P3_Next -->|是| P3_Chapter
    P3_Next -->|否| Phase4
    
    Phase4[Phase 4: Review 全文审核]
    P3_Next -->|完成所有章节| P4_Submit[提交审核任务到 Redis]
    P4_Submit --> P4_Wait[轮询等待结果]
    P4_Wait --> P4_Check{任务完成?}
    P4_Check -->|否| P4_Wait
    P4_Check -->|是| P4_Result[获取审核报告]
    P4_Result --> P4_Show[展示审核报告]
    P4_Show --> P4_Save[保存课程文档]
    P4_Save --> EndComplete([🎉 流程完成])
```

Worker 端处理流程

```mermaid

flowchart TD
    WorkerStart([Worker 启动]) --> Init[初始化 Redis 连接]
    Init --> StartLoop[启动 Worker 循环]
    StartLoop --> Fetch[安全获取任务<br/>RPOPLPUSH]
    
    Fetch --> CheckEmpty{队列有任务?}
    CheckEmpty -->|否| Sleep[等待 1 秒]
    Sleep --> Fetch
    CheckEmpty -->|是| ParseTask[解析任务数据]
    
    ParseTask --> CheckDone{任务已完成?}
    CheckDone -->|是| Ack1[ACK 确认]
    Ack1 --> Fetch
    
    CheckDone -->|否| AcquireLock{获取分布式锁}
    AcquireLock -->|失败| Ack2[ACK 并跳过]
    Ack2 --> Fetch
    
    AcquireLock -->|成功| Heartbeat[启动心跳保活]
    Heartbeat --> UpdateState1[更新状态: running]
    UpdateState1 --> Execute[执行 Agent 任务]
    
    Execute --> CheckRetry{执行成功?}
    CheckRetry -->|否| ShouldRetry{需要重试?}
    ShouldRetry -->|是| Backoff[指数退避等待]
    Backoff --> UpdateState2[更新状态: retrying]
    UpdateState2 --> Execute
    ShouldRetry -->|否| MarkFail[标记失败]
    
    CheckRetry -->|是| MarkSuccess[标记成功]
    
    MarkFail --> GrpcFail[gRPC 上报失败]
    MarkSuccess --> GrpcSuccess[gRPC 上报成功]
    
    GrpcFail --> ReleaseLock[释放锁]
    GrpcSuccess --> ReleaseLock
    ReleaseLock --> StopHeartbeat[停止心跳]
    StopHeartbeat --> Ack3[ACK 确认<br/>从队列移除]
    Ack3 --> Fetch
```



## 🛠️ 技术栈

### 核心技术

- **Redis**: 任务队列、状态存储、分布式锁
- **gRPC**: 服务间通信、结果回传
- **Python**: 主要开发语言
- **Protocol Buffers**: gRPC 数据序列化

### AI 框架

- **DashScope**: 阿里云通义千问 API
- **LangChain**: Agent 编排框架
- **FastMCP**: MCP 协议支持

### 关键组件

| 组件                | 文件                           | 功能               |
| ------------------- | ------------------------------ | ------------------ |
| TaskProcessor       | `extend/task_processor.py`     | 任务队列管理       |
| StateSynchronizer   | `extend/state_synchronizer.py` | 分布式锁和状态同步 |
| RetryManager        | `extend/retry_manager.py`      | 失败重试策略       |
| GrpcClient          | `extend/grpc_client.py`        | gRPC 客户端        |
| CourseAgentExecutor | `extend/agent_executor.py`     | AI Agent 执行器    |
| RedisManager        | `utils/redis_client.py`        | Redis 连接管理     |

### 技术难点

✅ **任务不丢失**
- Redis 持久化存储：Worker 宕机后任务仍在 processing_queue
- 安全获取（RPOPLPUSH）：任务从源队列移动到处理队列是原子的
- 遗留任务恢复机制：启动时自动检查并重新处理

✅ **避免重复执行**
- 分布式锁（基于 Redis）：SET NX 确保同一时刻只有一个 Worker 持有锁
- 幂等性检查：执行前检查 task:{id}:state.status == 'completed' 
- 任务状态追踪：锁超时机制：TTL=300s 防止死锁

✅ **跨服务状态同步**
- Redis Hash 存储状态：所有 Worker 共享 task:{id}:state
- gRPC 实时上报：running → completed/failed/retrying 状态变更立即写入
- 心跳保活机制：客户端轮询：submit_task_and_wait 每秒检查状态

✅ **失败重试**
- 指数退避算法：delay = base_delay * 2^retries + jitter
- 可配置重试次数：默认 3 次
- 详细日志记录：每次重试更新 retry_count 到 Redis

---



健壮的分布式处理流程：
1.*幂等性检查* *(Idempotency):* *检查任务是否已完成，避免重复消费。
2.* *分布式锁* *(Distributed Lock):* *确保同一时刻只有一个* *Worker* *处理该任务。
3.* *状态同步* *(State Sync):* *将任务状态* *(running/completed/failed)* *实时同步到* *Redis，供前端或监控查询。
4.* *结果上报* *(Result Reporting):* *通过* *gRPC* *将结果回传给主服务。
5.* *消息确认* *(ACK):* *处理完成后从* *Redis* *队列移除消息。*



```mermaid

flowchart TD
    subgraph UserLayer["👤 用户交互层"]
        UserInput["用户输入<br/>主题和要求"]
        UserChoice["用户选择/确认"]
    end

    subgraph ProducerLayer["📤 Producer 层 (produce_task.py)"]
        CourseClient["CourseGenerationClient"]
        SubmitTask["submit_task_and_wait()"]
        PushRedis["rpush 任务到 Redis"]
        PollState["轮询任务状态<br/>hgetall task:{id}:state"]
        CheckResult{"状态判断"}
        ShowResult["展示结果"]
    end

    subgraph RedisLayer["📦 Redis 中间件层"]
        TaskQueue["任务队列<br/>tasks:default"]
        ProcessingQueue["处理队列<br/>tasks:processing:{worker_id}"]
        TaskState["任务状态<br/>Hash: task:{id}:state<br/>- status<br/>- result<br/>- last_update"]
        DistributedLock["分布式锁<br/>lock:task:{id}<br/>TTL: 300s"]
    end

    subgraph WorkerLayer["🔧 Worker 层 (main.py)"]
        CourseSystem["CourseSystem<br/>run()"]
        StartWorker["start_worker()"]
        SafeFetch["safe_fetch()<br/>RPOPLPUSH"]
        ProcessLeftovers["_process_leftovers()"]
        HandleTask["_handle_task()"]
    end

    subgraph TaskProcessLayer["⚙️ 任务处理层"]
        CheckCompleted{"检查是否已完成<br/>get_state()"}
        AcquireLock{"获取分布式锁<br/>acquire_lock()"}
        StartHeartbeat["启动心跳线程<br/>threading.Thread()"]
        UpdateRunning["同步状态: running<br/>sync_state()"]
        ExecuteRetry["_process_task_with_retry()"]
        UpdateCompleted["同步状态: completed"]
        UpdateFailed["同步状态: failed"]
        GrpcReport["gRPC 上报<br/>report_result()"]
        ReleaseLock["释放锁<br/>release_lock()"]
        StopHeartbeat["停止心跳<br/>stop_heartbeat.set()"]
        AckTask["ACK 确认<br/>remove_from_processing()"]
    end

    subgraph RetryLayer[" 重试管理层"]
        RetryLoop{"重试循环"}
        AgentExecute["agent_executor.execute()"]
        ShouldRetry["should_retry()?"]
        LogFailure["log_failure()"]
        BackoffWait["wait_for_retry()<br/>指数退避"]
        UpdateRetrying["同步状态: retrying"]
    end

    subgraph AgentLayer["🤖 AI Agent 执行层"]
        AgentExecutor["CourseAgentExecutor"]
        CreateAgent["_create_agent()"]
        CreateTask["_create_task()"]
        CrewKickoff["Crew().kickoff()"]
        GetOutput["_get_agent_output()"]
    end

    subgraph Agents["AI Agents"]
        ResearchAgent[" xiao_mei<br/>Research Agent"]
        OutlineAgent["📝 xiao_qing<br/>Outline Agent"]
        ChapterAgent["️ xiao_qing<br/>Chapter Agent"]
        ReviewAgent["✅ xiao_yin<br/>Review Agent"]
    end

    subgraph GrpcLayer["🌐 gRPC 通信层"]
        GrpcClient["GrpcClient<br/>TaskServiceStub"]
        ReportSuccess["ReportResult SUCCESS"]
        ReportFailure["ReportResult FAILURE"]
    end

    subgraph HeartbeatLayer["💓 心跳保活层"]
        HeartbeatLoop["_heartbeat_loop()"]
        UpdateTimestamp["更新 last_update"]
        RefreshLock["刷新锁 TTL: 300s<br/>expire lock:task:{id}"]
    end

    %% 数据流
    UserInput --> CourseClient
    CourseClient --> SubmitTask
    SubmitTask --> PushRedis
    PushRedis --> TaskQueue
    PushRedis --> PollState
    PollState --> TaskState
    TaskState --> CheckResult
    
    CheckResult -->|completed| ShowResult
    CheckResult -->|failed| ShowResult
    CheckResult -->|retrying| PollState
    CheckResult -->|running| PollState
    
    ShowResult --> UserChoice
    
    %% Worker 启动
    CourseSystem --> StartWorker
    StartWorker --> ProcessLeftovers
    ProcessLeftovers --> TaskQueue
    StartWorker --> SafeFetch
    SafeFetch --> TaskQueue
    SafeFetch --> ProcessingQueue
    ProcessingQueue --> HandleTask
    
    %% 任务处理流程
    HandleTask --> CheckCompleted
    CheckCompleted -->|已完成| AckTask
    CheckCompleted -->|未完成| AcquireLock
    AcquireLock -->|失败| AckTask
    AcquireLock -->|成功| StartHeartbeat
    StartHeartbeat --> HeartbeatLoop
    StartHeartbeat --> UpdateRunning
    UpdateRunning --> ExecuteRetry
    
    ExecuteRetry --> RetryLoop
    RetryLoop --> AgentExecute
    AgentExecute -->|成功| UpdateCompleted
    AgentExecute -->|失败| ShouldRetry
    ShouldRetry -->|是| LogFailure
    LogFailure --> BackoffWait
    BackoffWait --> UpdateRetrying
    UpdateRetrying --> RetryLoop
    ShouldRetry -->|否| UpdateFailed
    
    UpdateCompleted --> GrpcReport
    UpdateFailed --> GrpcReport
    
    GrpcReport -->|成功| ReportSuccess
    GrpcReport -->|失败| ReportFailure
    ReportSuccess --> GrpcClient
    ReportFailure --> GrpcClient
    GrpcClient --> PollState
    
    UpdateCompleted --> ReleaseLock
    UpdateFailed --> ReleaseLock
    ReleaseLock --> StopHeartbeat
    ReleaseLock --> HeartbeatLoop
    StopHeartbeat --> AckTask
    
    %% Agent 执行
    AgentExecute --> AgentExecutor
    AgentExecutor --> CreateAgent
    CreateAgent --> ResearchAgent
    CreateAgent --> OutlineAgent
    CreateAgent --> ChapterAgent
    CreateAgent --> ReviewAgent
    AgentExecutor --> CreateTask
    CreateTask --> CrewKickoff
    CrewKickoff --> GetOutput
    
    %% 心跳机制
    HeartbeatLoop --> UpdateTimestamp
    UpdateTimestamp --> TaskState
    UpdateTimestamp --> RefreshLock
    RefreshLock --> DistributedLock
    
    %% 样式
    style UserLayer fill:#e1f5ff
    style ProducerLayer fill:#fff3cd
    style RedisLayer fill:#f8d7da
    style WorkerLayer fill:#d4edda
    style TaskProcessLayer fill:#d1ecf1
    style RetryLayer fill:#ffe5b4
    style AgentLayer fill:#e2d5f1
    style Agents fill:#f1d5e2
    style GrpcLayer fill:#d5e8f1
    style HeartbeatLayer fill:#f1f5d5
```

