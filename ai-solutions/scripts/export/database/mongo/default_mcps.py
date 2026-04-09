from datetime import datetime
from bson import ObjectId

DEFAULT_MCPS = [
    {
        "_id": ObjectId("6894bc021791731bebbe9146"),
        "name": "Gmail",
        "description": "Servidor MCP para integração com Gmail",
        "img_url": "https://images.icon-icons.com/2631/PNG/512/gmail_new_logo_icon_159149.png",
        "created_at": datetime(2025, 8, 7, 14, 45, 22, 127000),
        "updated_at": datetime(2025, 8, 7, 14, 45, 22, 127000),
    },
    {
        "_id": ObjectId("6894cab9bcf1dbe10ca8b0da"),
        "name": "GitHub",
        "description": "Code hosting platform for version control, collaboration, issue tracking, and CI.",
        "img_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
        "created_at": datetime(2025, 8, 7, 15, 48, 9, 757000),
        "updated_at": datetime(2025, 8, 7, 15, 48, 9, 757000),
    },
    {
        "_id": ObjectId("6894cabbbcf1dbe10ca8b0db"),
        "name": "Google Calendar",
        "description": "Time management tool with scheduling, reminders and email integration.",
        "img_url": "https://upload.wikimedia.org/wikipedia/commons/a/a5/Google_Calendar_icon_%282020%29.svg",
        "created_at": datetime(2025, 8, 7, 15, 48, 11, 821000),
        "updated_at": datetime(2025, 8, 7, 15, 48, 11, 821000),
    },
    {
        "_id": ObjectId("6894cabdbcf1dbe10ca8b0dc"),
        "name": "Notion",
        "description": "Workspace centralizing notes, docs, wikis and tasks for collaboration.",
        "img_url": "https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png",
        "created_at": datetime(2025, 8, 7, 15, 48, 13, 877000),
        "updated_at": datetime(2025, 8, 7, 15, 48, 13, 877000),
    },
    {
        "_id": ObjectId("6894cabfbcf1dbe10ca8b0dd"),
        "name": "Google Sheets",
        "description": "Cloud-based spreadsheet tool for real-time collaboration and analytics.",
        "img_url": "https://cdn.jsdelivr.net/gh/ComposioHQ/open-logos@master/google-sheets.svg",
        "created_at": datetime(2025, 8, 7, 15, 48, 15, 916000),
        "updated_at": datetime(2025, 8, 7, 15, 48, 15, 916000),
    },
    {
        "_id": ObjectId("6894cac1bcf1dbe10ca8b0de"),
        "name": "Slack",
        "description": "Channel-based messaging platform for team collaboration.",
        "img_url": "https://upload.wikimedia.org/wikipedia/commons/7/76/Slack_Icon.png",
        "created_at": datetime(2025, 8, 7, 15, 48, 17, 979000),
        "updated_at": datetime(2025, 8, 7, 15, 48, 17, 979000),
    },
    {
        "_id": ObjectId("6894cac4bcf1dbe10ca8b0df"),
        "name": "Linear",
        "description": "Issue tracking and project planning tool with fast workflows.",
        "img_url": "https://cdn.jsdelivr.net/gh/ComposioHQ/open-logos@master/linear.png",
        "created_at": datetime(2025, 8, 7, 15, 48, 20, 37000),
        "updated_at": datetime(2025, 8, 7, 15, 48, 20, 37000),
    },
    {
        "_id": ObjectId("6894cac6bcf1dbe10ca8b0e0"),
        "name": "Trello",
        "description": "Kanban-style list-making application for task management.",
        "img_url": "https://cdn.jsdelivr.net/gh/ComposioHQ/open-logos@master/trello.svg",
        "created_at": datetime(2025, 8, 7, 15, 48, 22, 113000),
        "updated_at": datetime(2025, 8, 7, 15, 48, 22, 113000),
    },
]
