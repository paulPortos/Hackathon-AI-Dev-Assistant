KANBAN_FUNCTION_DECLARATIONS = [
    {
        "name": "kanban_list_boards",
        "description": "List all Kanban boards. Returns board names and IDs.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "kanban_get_board_detail",
        "description": "Get full board state including all columns and cards.",
        "parameters": {
            "type": "object",
            "properties": {
                "board_id": {"type": "integer", "description": "The board ID to fetch"}
            },
            "required": ["board_id"]
        }
    },
    {
        "name": "kanban_add_card",
        "description": "Add a new card to a column on the Kanban board.",
        "parameters": {
            "type": "object",
            "properties": {
                "column_id": {"type": "integer", "description": "Target column ID"},
                "title": {"type": "string", "description": "Card title"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "description": {"type": "string", "description": "Card description"},
                "due_date": {"type": "string", "description": "Due date in ISO 8601 format (e.g., '2026-05-06T12:00:00Z')"}
            },
            "required": ["column_id", "title"]
        }
    },
    {
        "name": "kanban_move_card",
        "description": "Move a card to a different column.",
        "parameters": {
            "type": "object",
            "properties": {
                "card_id": {"type": "integer", "description": "Card ID to move"},
                "target_column_id": {"type": "integer", "description": "Target column ID"}
            },
            "required": ["card_id", "target_column_id"]
        }
    },
    {
        "name": "kanban_update_card",
        "description": "Update a card's title, description, priority, or due_date.",
        "parameters": {
            "type": "object",
            "properties": {
                "card_id": {"type": "integer", "description": "Card ID to update"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "due_date": {"type": "string", "description": "Due date in ISO 8601 format (e.g., '2026-05-06T12:00:00Z')"}
            },
            "required": ["card_id"]
        }
    },
    {
        "name": "kanban_delete_card",
        "description": "Delete a card from the Kanban board.",
        "parameters": {
            "type": "object",
            "properties": {
                "card_id": {"type": "integer", "description": "Card ID to delete"}
            },
            "required": ["card_id"]
        }
    },
    {
        "name": "kanban_bulk_move_cards",
        "description": "Move multiple cards to a different column simultaneously.",
        "parameters": {
            "type": "object",
            "properties": {
                "card_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of Card IDs to move"
                },
                "target_column_id": {"type": "integer", "description": "Target column ID"}
            },
            "required": ["card_ids", "target_column_id"]
        }
    },
    {
        "name": "kanban_bulk_update_cards",
        "description": "Update multiple cards at once (e.g., bulk set due date or priority).",
        "parameters": {
            "type": "object",
            "properties": {
                "card_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of Card IDs to update"
                },
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "due_date": {"type": "string", "description": "Due date in ISO 8601 format (e.g., '2026-05-06T12:00:00Z')"}
            },
            "required": ["card_ids"]
        }
    }
]
