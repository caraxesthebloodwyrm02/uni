from mcp.server.fastmcp import FastMCP  # type: ignore

try:
    from . import apparat_logic  # type: ignore
except ImportError:
    import apparat_logic  # type: ignore

# Create the MCP server
mcp = FastMCP("Apparat-Server")


@mcp.tool()
def check_apparat_health():
    """
    Performs a full SISA bootstrap health check of the Apparat subsystem.
    Returns components status, resolved phases, and any architectural warnings.
    """
    return apparat_logic.check_apparat_health()


@mcp.tool()
def get_apparat_state(width: int = 4, height: int = 4):
    """
    Retrieves the current state of the global Apparat processor,
    including resolution and the last successfully executed phase.
    """
    return apparat_logic.get_apparat_state(width, height)


@mcp.tool()
def list_apparat_phases():
    """
    Returns a list of all currently registered phase handlers in the Apparat registry.
    """
    return apparat_logic.list_apparat_phases()


@mcp.tool()
def run_apparat_phase(phase: str, width: int = 4, height: int = 4):
    """
    Executes a specific Apparat phase processing step.

    Args:
        phase: The phase name (e.g., 'initiate', 'scale:2.0', 'clamp:0.1,0.9').
        width: The grid width for the processor.
        height: The grid height for the processor.
    """
    return apparat_logic.run_apparat_phase(phase, width, height)


@mcp.tool()
def run_apparat_pipeline(pipeline: str, width: int = 4, height: int = 4):
    """
    Executes a sequence of Apparat phase processing steps in a single call.

    Args:
        pipeline: A slash-separated sequence of phases (e.g., 'initiate/scale:2.0/complete').
        width: The grid width for the processor.
        height: The grid height for the processor.
    """
    return apparat_logic.run_apparat_pipeline(pipeline, width, height)


@mcp.tool()
def search_constraints(query: str | None = None):
    """
    Locates systemic constraints, rules, and limits embedded in the codebase
    via natural language, programmatic regexes, and numerical constants.

    Args:
        query: Optional regex to filter the findings.
    """
    return apparat_logic.search_constraints(query)


if __name__ == "__main__":
    mcp.run()
