from mcp.server.mcpserver import MCPServer

# Create the server, give it a name
mcp = MCPServer("jobtrail")

# This is our one dummy tool, just to prove things work
@mcp.tool()
def say_hello(name: str) -> str:
    """Say hello to someone by name."""
    return f"Hello, {name}! JobTrail server is working."

# This runs the server when we execute this file directly
if __name__ == "__main__":
    mcp.run()