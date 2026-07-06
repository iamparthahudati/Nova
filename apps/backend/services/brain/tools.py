"""Tool schema (fed to Claude for routing) and the tool-execution dispatcher.

The concrete implementation behind each tool (WhatsApp, calendar, weather,
habits, and so on) lives outside Brain — callers pass in a `handlers` dict
mapping tool name -> a function that takes the tool's input dict and returns
the spoken-response string. Brain only knows how to look one up and call it.
"""

from typing import Callable

ToolHandler = Callable[[dict], str]

ASSISTANT_TOOLS = [
    {
        "name": "send_whatsapp_message",
        "description": (
            "Send (or draft) a WhatsApp message to a named contact. "
            "Use when the user says 'message X on WhatsApp', 'WhatsApp X', 'send X a message', etc. "
            "Opens WhatsApp with the message pre-filled; user confirms by pressing Send."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "contact": {
                    "type": "string",
                    "description": "Contact name as it appears in Contacts",
                },
                "message": {"type": "string", "description": "Text of the message to send"},
            },
            "required": ["contact", "message"],
        },
    },
    {
        "name": "open_app",
        "description": (
            "Open a macOS application or website. "
            "ONLY call this when the user explicitly wants to launch, open, or start an app or site — "
            "NOT when they are merely mentioning, asking about, or referencing one."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "App keyword (e.g. 'chrome', 'spotify', 'whatsapp', 'terminal') or full URL",
                }
            },
            "required": ["target"],
        },
    },
    {
        "name": "add_task",
        "description": "Log a new open task or to-do item",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Task description"},
                "due": {
                    "type": "string",
                    "description": "Due date as natural language ('Friday', 'July 10') or ISO YYYY-MM-DD; omit if none",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "complete_task",
        "description": "Mark an existing open task as done",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Partial text to match the task"}
            },
            "required": ["text"],
        },
    },
    {
        "name": "add_money",
        "description": "Log income (earned) or an expense (spent)",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["earned", "spent"]},
                "amount": {"type": "number"},
                "note": {
                    "type": "string",
                    "description": "Optional description of the transaction",
                },
            },
            "required": ["type", "amount"],
        },
    },
    {
        "name": "add_progress",
        "description": "Log a progress note",
        "input_schema": {
            "type": "object",
            "properties": {
                "note": {"type": "string"},
                "area": {
                    "type": "string",
                    "description": "Optional category (e.g. 'work', 'health')",
                },
            },
            "required": ["note"],
        },
    },
    {
        "name": "add_product",
        "description": "Add a new product or side-project to track",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "store": {"type": "string"},
                "price": {"type": "number"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "ship_product",
        "description": "Mark a product or project as shipped or launched",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
    {
        "name": "log_sale",
        "description": "Log a sale for an existing product",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
    {
        "name": "add_calendar_event",
        "description": "Create a new event in macOS Calendar",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "date": {
                    "type": "string",
                    "description": "Natural-language date ('July 10', 'next Friday') or ISO YYYY-MM-DD",
                },
                "time": {
                    "type": "string",
                    "description": "Time in 12h or 24h format (e.g. '4pm', '16:00'); omit for all-day",
                },
            },
            "required": ["title", "date"],
        },
    },
    {
        "name": "get_events",
        "description": "Get calendar events for a specific day",
        "input_schema": {
            "type": "object",
            "properties": {
                "day": {
                    "type": "string",
                    "description": "Natural-language date or ISO YYYY-MM-DD; defaults to today if omitted",
                }
            },
        },
    },
    {
        "name": "add_reminder",
        "description": (
            "Save a reminder that will surface on a specific date, optionally at a specific time. "
            "Resolve relative dates ('tomorrow', 'next Friday') against today's date from context. "
            "For relative offsets ('in 20 minutes', 'after 2 hours', 'in 3 days'), pass the "
            "expression verbatim as remind_date — the system resolves it against the current "
            "clock. Never ask the user for the current date or time."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "remind_date": {
                    "type": "string",
                    "description": (
                        "Date in ISO format YYYY-MM-DD (e.g. '2026-07-06'), or a verbatim "
                        "relative offset like 'in 20 minutes' or 'after 2 hours'"
                    ),
                },
                "remind_time": {
                    "type": "string",
                    "description": "Time of day in 24h HH:MM (e.g. '06:00'); omit for a day-level reminder",
                },
            },
            "required": ["text", "remind_date"],
        },
    },
    {
        "name": "get_weather",
        "description": "Get the current weather",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name; omit to use the default configured location",
                }
            },
        },
    },
    {
        "name": "get_github_notifications",
        "description": "Get unread GitHub notifications",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_rss_updates",
        "description": "Get latest RSS feed headlines",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "run_reflection",
        "description": "Run the weekly profile reflection job to update observed patterns",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "journal",
        "description": "Log a reflective journal entry and get a thoughtful response",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
    # Phase 13 tools
    {
        "name": "log_habit",
        "description": "Log that a daily habit was completed today (e.g. 'I did my workout', 'logged habit meditation')",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the habit (e.g. 'workout', 'meditation', 'reading')",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_habits",
        "description": "Get the list of habits logged today",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "start_pomodoro",
        "description": "Start a focus/Pomodoro timer that notifies when time is up",
        "input_schema": {
            "type": "object",
            "properties": {
                "minutes": {"type": "integer", "description": "Duration in minutes (default 25)"},
            },
        },
    },
    {
        "name": "read_my_day",
        "description": "Give a full spoken rundown of today: calendar, tasks, reminders, habits, progress notes, and money",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_spending_summary",
        "description": "Get an earnings/spending summary for a time period",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["today", "this week", "last week", "this month"],
                    "description": "Time window for the summary",
                },
            },
        },
    },
]


def execute(name: str, args: dict, handlers: dict[str, ToolHandler]) -> str:
    """Look up and invoke the handler for a tool call chosen by Claude."""
    handler = handlers.get(name)
    if handler is None:
        return f"Unknown tool: {name}"
    return handler(args)
