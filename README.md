# TimeLiner MCP Server

TimeLiner 项目管理系统的 MCP (Model Context Protocol) Server，让 AI 客户端通过 MCP 协议操控项目管理。

## 前置条件

- Python 3.11+
- TimeLiner 后端服务运行在 `localhost:8080`
- 安装依赖：

```bash
cd TimeLiner/mcp_server
pip install -r requirements.txt
```

## 启动后端

```bash
cd TimeLiner/backend
uvicorn main:app --reload --port 8080
```

## 客户端接入

### stdio 模式（推荐）

适用于 Claude Desktop、Cursor、Kiro 等本地 AI 客户端。

在客户端 MCP 配置文件中添加（通过环境变量传入用户名密码，连接时自动登录）：

```json
{
  "mcpServers": {
    "timeliner": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "D:/demo/TimeLiner",
      "env": {
        "TIMELINER_BACKEND_URL": "http://localhost:8080/api",
        "TIMELINER_USERNAME": "li.ming.pm",
        "TIMELINER_PASSWORD": "Demo@12345"
      }
    }
  }
}
```

配置文件位置：

| 客户端 | 路径 |
|--------|------|
| Claude Desktop | `%APPDATA%/Claude/claude_desktop_config.json` |
| Kiro | `.kiro/settings/mcp.json` |
| Cursor | `.cursor/mcp.json` |

### SSE 模式（远程/多客户端）

```bash
cd TimeLiner
TIMELINER_USERNAME=li.ming.pm TIMELINER_PASSWORD=Demo@12345 \
  python -m mcp_server.server --transport sse --port 8888
```

客户端配置：

```json
{
  "mcpServers": {
    "timeliner": {
      "url": "http://localhost:8888/sse"
    }
  }
}
```

### 鉴权说明

- 配置 `TIMELINER_USERNAME` + `TIMELINER_PASSWORD` 环境变量后，MCP Server 启动时自动登录，无需手动调用 `login`
- 如果未配置环境变量，可以通过 `login` tool 手动登录
- 已登录状态下调用 `login` 可切换用户身份
- 调用 `whoami` 可查看当前登录状态

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TIMELINER_BACKEND_URL` | `http://localhost:8080/api` | 后端 API 地址 |
| `TIMELINER_REQUEST_TIMEOUT` | `30` | HTTP 请求超时（秒） |
| `TIMELINER_USERNAME` | _(空)_ | 自动登录用户名 |
| `TIMELINER_PASSWORD` | _(空)_ | 自动登录密码 |

## Tool 清单（47 个）

### 认证（3）

| Tool | 说明 | 角色 |
|------|------|------|
| `login` | 手动登录 / 切换用户（通常不需要） | Public |
| `get_current_user` | 获取当前用户信息 | Both |
| `whoami` | 查看当前登录状态 | Public |

### 项目管理（6）

| Tool | 说明 | 角色 |
|------|------|------|
| `create_project` | 创建项目 | Admin |
| `list_projects` | 列出项目 | Both |
| `get_project` | 项目详情 | Both |
| `update_project` | 更新项目 | Admin |
| `delete_project` | 删除项目 | Admin |
| `get_project_dashboard` | 时间线仪表盘 | Both |

### 任务管理（8）

| Tool | 说明 | 角色 |
|------|------|------|
| `create_task` | 创建任务 | Admin |
| `list_tasks` | 列出任务 | Both |
| `get_task` | 任务详情 | Both |
| `update_task` | 更新任务 | Admin |
| `delete_task` | 删除任务 | Admin |
| `add_task_dependency` | 添加依赖 | Admin |
| `ai_split_task` | AI 拆分任务 | Admin |
| `confirm_and_distribute_tasks` | 批量分发任务 | Admin |

### 成员管理（6）

| Tool | 说明 | 角色 |
|------|------|------|
| `add_member` | 添加成员 | Admin |
| `list_members` | 列出成员 | Both |
| `get_member` | 成员详情 | Both |
| `update_member` | 更新成员 | Admin |
| `remove_member` | 移除成员 | Admin |
| `list_member_skills` | 查看技能 | Both |

### 技能管理（2）

| Tool | 说明 | 角色 |
|------|------|------|
| `add_member_skill` | 添加技能 | Admin |
| `remove_member_skill` | 移除技能 | Admin |

### 里程碑（5）

| Tool | 说明 | 角色 |
|------|------|------|
| `create_milestone` | 创建里程碑 | Admin |
| `list_milestones` | 列出里程碑 | Both |
| `get_milestone` | 里程碑详情 | Both |
| `update_milestone` | 更新里程碑 | Admin |
| `delete_milestone` | 删除里程碑 | Admin |

### 邀请管理（4）

| Tool | 说明 | 角色 |
|------|------|------|
| `create_invitation` | 创建邀请码 | Admin |
| `list_invitations` | 查看邀请列表 | Admin |
| `revoke_invitation` | 撤销邀请 | Admin |
| `accept_invitation` | 接受邀请 | User |

### 调度管理（5）

| Tool | 说明 | 角色 |
|------|------|------|
| `list_schedule_requests` | 查看调度申请 | Admin |
| `approve_schedule_request` | 批准申请 | Admin |
| `reject_schedule_request` | 拒绝申请 | Admin |
| `request_schedule_change` | 发起调度申请 | User |
| `get_my_schedule_requests` | 查看我的申请 | User |

### 决策（2）

| Tool | 说明 | 角色 |
|------|------|------|
| `validate_decision` | 验证决策 | Admin |
| `apply_decision` | 应用决策 | Admin |

### 用户任务（4）

| Tool | 说明 | 角色 |
|------|------|------|
| `get_my_tasks` | 我的任务列表 | User |
| `get_today_goals` | 今日目标 | User |
| `update_task_progress` | 更新进度 | User |
| `submit_task_completion` | 提交完成 | User |

### 上下文查询（3）

| Tool | 说明 | 角色 |
|------|------|------|
| `get_project_context` | 项目 Markdown 上下文 | Both |
| `get_task_context` | 任务 Markdown 上下文 | Both |
| `get_project_activities` | 项目活动日志 | Both |

## 典型使用流程

### Admin：AI 辅助任务拆分

连接时已自动登录（env 配置 `li.ming.pm` / `Demo@12345`），直接使用：

```
1. create_project("用户认证模块", "2026-04-01T00:00:00Z", "2026-05-01T00:00:00Z")
2. add_member(project_id, "张三")
3. ai_split_task(project_id, "实现登录、注册、密码重置、OAuth2")
   → 返回 prompt，客户端 LLM 生成子任务方案
4. confirm_and_distribute_tasks(project_id, task_plan)
   → 批量创建任务、设依赖、验证、应用决策
```

### User：日常任务管理

连接时已自动登录（env 配置 `chen.yan.dev` / `Demo@12345`），直接使用：

```
1. get_today_goals(project_id)
   → 按优先级 + 关键路径排序的待办任务
2. update_task_progress(task_id, 0.6)
3. submit_task_completion(task_id)
```

## 运行测试

```bash
cd TimeLiner
python -m pytest mcp_server/tests/ -v
```

## 架构说明

```
MCP Client (Claude/Cursor/Kiro)
    ↕ MCP 协议 (stdio/SSE)
MCP Server (FastMCP)
    ↕ HTTP (httpx)
TimeLiner Backend (FastAPI :8080)
    ↕ SQLAlchemy
PostgreSQL / SQLite
```

MCP Server 不直接访问数据库，所有操作通过后端 HTTP API 完成，保持架构分层。
