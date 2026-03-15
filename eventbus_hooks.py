"""EventBus hooks for new event types + feishu TODO placeholders."""

from backend.eventbus.event_bus import Event, EventBus


async def handle_task_created(event: Event) -> None:
    """任务创建后触发。"""
    # TODO: 接入飞书 API — 为负责人创建飞书 TODO
    return


async def handle_task_distributed(event: Event) -> None:
    """AI 拆分确认分发后触发。"""
    # TODO: 接入飞书 API — 批量创建飞书 TODO
    return


async def handle_task_completed_by_user(event: Event) -> None:
    """用户提交任务完成后触发。"""
    # TODO: 接入飞书 API — 标记飞书 TODO 完成
    return


async def handle_milestone_created(event: Event) -> None:
    """创建里程碑后触发。"""
    # TODO: 接入飞书 API — 通知项目群
    return


async def handle_schedule_approved_feishu(event: Event) -> None:
    """调度审批通过后触发。"""
    # TODO: 接入飞书 API — 通知申请人审批通过
    return


async def handle_schedule_rejected_feishu(event: Event) -> None:
    """调度审批拒绝后触发。"""
    # TODO: 接入飞书 API — 通知申请人被拒原因
    return


async def handle_progress_submitted_feishu(event: Event) -> None:
    """进度提交后触发。"""
    # TODO: 接入飞书 API — 更新飞书 TODO 进度
    return


async def handle_critical_path_changed_feishu(event: Event) -> None:
    """关键路径变化后触发。"""
    # TODO: 接入飞书 API — 通知项目群关键路径变化
    return


async def handle_conflict_detected_feishu(event: Event) -> None:
    """冲突检测后触发。"""
    # TODO: 接入飞书 API — 告警 Admin 资源冲突
    return


def register_mcp_event_handlers(bus: EventBus) -> None:
    """注册 MCP Server 新增的事件处理函数。"""
    bus.subscribe("TaskCreated", handle_task_created)
    bus.subscribe("TaskDistributed", handle_task_distributed)
    bus.subscribe("TaskCompletedByUser", handle_task_completed_by_user)
    bus.subscribe("MilestoneCreated", handle_milestone_created)
    # 飞书钩子补充（挂载到已有事件）
    bus.subscribe("ScheduleApproved", handle_schedule_approved_feishu)
    bus.subscribe("ScheduleRejected", handle_schedule_rejected_feishu)
    bus.subscribe("ProgressSubmitted", handle_progress_submitted_feishu)
    bus.subscribe("CriticalPathChanged", handle_critical_path_changed_feishu)
    bus.subscribe("ConflictDetected", handle_conflict_detected_feishu)
