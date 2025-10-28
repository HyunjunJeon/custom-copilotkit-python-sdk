"""
Sample actions for testing

Provides reusable sample Action objects for testing.
"""
from copilotkit import Action, Parameter


def create_simple_action():
    """Create a simple action without parameters"""
    def handler():
        return {"result": "success"}

    return Action(
        name="simple_action",
        description="A simple test action",
        parameters=[],
        handler=handler
    )


def create_action_with_parameters():
    """Create an action with required parameters"""
    def handler(query: str, limit: int = 10):
        return {
            "query": query,
            "limit": limit,
            "results": [f"result_{i}" for i in range(limit)]
        }

    return Action(
        name="search_database",
        description="Search the database with a query",
        parameters=[
            Parameter(
                name="query",
                type="string",
                description="Search query",
                required=True
            ),
            Parameter(
                name="limit",
                type="number",
                description="Maximum number of results",
                required=False
            )
        ],
        handler=handler
    )


async def async_handler(data: str):
    """Async handler for testing"""
    return {"processed": data.upper()}


def create_async_action():
    """Create an action with async handler"""
    return Action(
        name="async_action",
        description="An async test action",
        parameters=[
            Parameter(
                name="data",
                type="string",
                description="Data to process",
                required=True
            )
        ],
        handler=async_handler
    )


def create_action_with_object_parameter():
    """Create an action with object type parameter"""
    def handler(config: dict):
        return {"config_received": config}

    return Action(
        name="configure_system",
        description="Configure system with object parameter",
        parameters=[
            Parameter(
                name="config",
                type="object",
                description="Configuration object",
                required=True
            )
        ],
        handler=handler
    )


def create_action_with_array_parameter():
    """Create an action with array type parameter"""
    def handler(items: list):
        return {"count": len(items), "items": items}

    return Action(
        name="process_list",
        description="Process a list of items",
        parameters=[
            Parameter(
                name="items",
                type="array",
                description="List of items to process",
                required=True
            )
        ],
        handler=handler
    )


def create_failing_action():
    """Create an action that raises an exception"""
    def handler():
        raise ValueError("Intentional test error")

    return Action(
        name="failing_action",
        description="An action that always fails",
        parameters=[],
        handler=handler
    )


def get_all_sample_actions():
    """Get list of all sample actions"""
    return [
        create_simple_action(),
        create_action_with_parameters(),
        create_async_action(),
        create_action_with_object_parameter(),
        create_action_with_array_parameter(),
    ]
