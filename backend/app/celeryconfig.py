from kombu import Queue, Exchange

# ─── Broker & Backend ──────────────────────────────────────────────────────
broker_transport_options = {
    "visibility_timeout": 3600,   # 1 hour — must exceed max grading time
    "fanout_prefix": True,
    "fanout_patterns": True,
    "socket_keepalive": True,
    "retry_on_timeout": True,
}

# ─── Queues ────────────────────────────────────────────────────────────────
task_queues = (
    Queue("high_priority", Exchange("high_priority"), routing_key="high_priority", queue_arguments={"x-max-priority": 10}),
    Queue("normal",        Exchange("normal"),        routing_key="normal"),
    Queue("regrade",       Exchange("regrade"),       routing_key="regrade"),
    Queue("cleanup",       Exchange("cleanup"),       routing_key="cleanup"),
)
task_default_queue = "normal"
task_default_exchange = "normal"
task_default_routing_key = "normal"

# ─── Routing ───────────────────────────────────────────────────────────────
task_routes = {
    "workers.tasks.grade_submission_task":       {"queue": "normal"},
    "workers.tasks.grade_submission_high":       {"queue": "high_priority"},
    "workers.tasks.regrade_submission":          {"queue": "regrade"},
    "workers.tasks.cleanup_workspace":           {"queue": "cleanup"},
}

# ─── Reliability ───────────────────────────────────────────────────────────
task_acks_late = True
task_reject_on_worker_lost = True
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# ─── Result TTL ────────────────────────────────────────────────────────────
result_expires = 86400

# ─── Timeouts ──────────────────────────────────────────────────────────────
task_soft_time_limit = 280
task_time_limit = 300

# ─── Worker ────────────────────────────────────────────────────────────────
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 200
worker_disable_rate_limits = False
