"""Nova's Memory service — the only module that touches nova.db.

Every other module (voice daemon, dashboard, future services) reads and
writes structured facts through this package's public functions. Nothing
outside memory/ should open a sqlite3 connection to nova.db directly.
"""

from .schema import init_db

from .health import ping_database, semantic_index_exists

from .tasks import (
    add_task,
    complete_task,
    complete_task_by_id,
    find_task_by_text,
    get_task_by_id,
    get_open_tasks,
    get_all_tasks,
    count_open_tasks,
    get_recent_tasks,
    get_recent_open_tasks,
    get_done_tasks_since,
    get_done_task_texts_for_date,
)

from .money import (
    add_money,
    get_latest_money,
    get_money_by_id,
    get_recent_money,
    get_money_since,
    get_money_totals_between,
    get_money_totals_for_date,
)

from .progress import (
    add_progress,
    get_recent_progress,
    get_progress_since,
    get_progress_notes_for_date,
)

from .products import (
    add_product,
    find_product_by_name,
    get_product_by_id,
    ship_product,
    log_sale,
    get_products,
)

from .reminders import (
    add_reminder,
    get_latest_reminder,
    get_reminder_by_id,
    get_due_reminders,
    get_upcoming_reminders,
    count_reminders,
    get_recent_reminders,
)

from .habits import (
    log_habit,
    get_latest_habit,
    get_habits_today,
    get_recent_habits,
)

from .profile import (
    get_profile_observations,
    get_last_profile_update,
    replace_profile_observations,
)

from .graph import (
    create_entity,
    get_entity,
    find_entity,
    delete_entity,
    link_entities,
    entity_edges,
    delete_edge,
    related_entities,
    list_graph_snapshot,
    graph_stats,
)

from .semantic import (
    remember,
    supersede_memory,
    recall,
    list_memories,
    count_active_memories,
    count_active_memories_by_tier,
    rebuild_index,
    maintenance,
    recalculate_scores,
    evaluate_memory,
    promote_memory,
    demote_memory,
    archive_memory,
    forget_memory,
    restore_memory,
    touch_memory,
    record_access,
    memories_pending_entity_extraction,
    record_entity_extraction_attempt,
    mark_entities_extracted,
)

__all__ = [
    "init_db",
    "ping_database",
    "semantic_index_exists",
    "add_task", "complete_task", "get_open_tasks", "get_all_tasks", "count_open_tasks",
    "get_recent_tasks", "get_recent_open_tasks", "get_done_tasks_since",
    "get_done_task_texts_for_date",
    "add_money", "get_recent_money", "get_money_since",
    "get_money_totals_between", "get_money_totals_for_date",
    "add_progress", "get_recent_progress", "get_progress_since",
    "get_progress_notes_for_date",
    "add_product", "ship_product", "log_sale", "get_products",
    "add_reminder", "get_due_reminders", "get_upcoming_reminders",
    "count_reminders", "get_recent_reminders",
    "log_habit", "get_habits_today", "get_recent_habits",
    "get_profile_observations", "get_last_profile_update",
    "replace_profile_observations",
    "create_entity", "get_entity", "find_entity", "delete_entity",
    "link_entities", "entity_edges", "delete_edge", "related_entities",
    "list_graph_snapshot", "graph_stats",
    "remember", "supersede_memory", "recall", "list_memories",
    "count_active_memories", "count_active_memories_by_tier", "rebuild_index",
    "maintenance", "recalculate_scores", "evaluate_memory",
    "promote_memory", "demote_memory", "archive_memory",
    "forget_memory", "restore_memory", "touch_memory", "record_access",
    "memories_pending_entity_extraction", "record_entity_extraction_attempt",
    "mark_entities_extracted",
]
