# AnswerRocket Multi-Copilot MCP Server

An MCP (Model Context Protocol) server that provides access to AnswerRocket's analytics and insights platform. This server automatically creates **separate MCP servers for each copilot** in your AnswerRocket instance, allowing dedicated, focused interactions with individual copilots through LLM clients.

## Features

- 🚀 **Multi-Copilot Architecture**: Automatically creates separate MCP servers for each copilot in your AnswerRocket instance
- 🎯 **Dedicated Copilot Servers**: Each copilot gets its own MCP server with copilot-specific tools and capabilities  
- 🤖 **Copilot Management**: Get information about individual copilots and their capabilities
- 🛠️ **Skill Operations**: List, inspect, and run specific skills within each copilot
- 💬 **Interactive Q&A**: Ask questions directly to specific AnswerRocket copilots and receive insights
- 📊 **Rich Responses**: Get both text responses and HTML artifacts for data visualizations

## Quick Install

Install the AnswerRocket MCP Server with a single command:

```bash
curl -fsSL https://raw.githubusercontent.com/AnswerrocketKW/mcp-test/refs/heads/main/install.sh -o /tmp/install.sh && bash /tmp/install.sh
```

The installer will:
1. Check system requirements (Python 3.8+, git, curl)
2. Prompt you for your AnswerRocket URL
3. Guide you to generate an API key from your AnswerRocket instance
4. Set up a Python virtual environment
5. Install all dependencies (including AnswerRocket SDK from git repository)
6. Discover all copilots in your AnswerRocket instance
7. Create and install separate MCP servers for each copilot

## Manual Installation

If you prefer to install manually:

### Prerequisites

- Python 3.8 or higher
- Git
- An AnswerRocket instance with API access

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/answerrocket/mcp-server-demo.git
   cd mcp-server-demo
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   pip install "git+ssh://git@github.com/answerrocket/answerrocket-python-client.git@get-copilots-for-mcp"
   ```

4. **Get your API credentials:**
   - Go to `{YOUR_AR_URL}/apps/chat/topics?panel=user-info`
   - Click "Generate" under "Client API Key"
   - Copy the generated API key

5. **Create copilot metadata script:**
   ```bash
   python get_copilots.py "{YOUR_AR_URL}" "{YOUR_API_TOKEN}"
   ```

6. **Install MCP servers for each copilot:**
   ```bash
   # This will create a separate server for each copilot
   mcp install server.py -n "answerrocket-copilot-{COPILOT_ID}" -v AR_URL="{YOUR_AR_URL}" -v AR_TOKEN="{YOUR_API_TOKEN}" -v COPILOT_ID="{COPILOT_ID}" --with "git+ssh://git@github.com/answerrocket/answerrocket-python-client.git@get-copilots-for-mcp"
   ```

## Available Tools (Per Copilot Server)

Each copilot gets its own dedicated MCP server with the following tools:

### `ask_question`
Ask a question to this specific AnswerRocket copilot and receive insights with visualizations.

**Parameters:**
- `fully_contextualized_question` (string): Your question with full context

### `get_copilot_info`
Get detailed information about this copilot, including its available skills.

**Parameters:**
- `use_published_version` (boolean, optional): Use published version (default: true)

### `get_skill_info`
Get detailed information about a specific skill within this copilot.

**Parameters:**
- `skill_id` (string): The ID of the skill
- `use_published_version` (boolean, optional): Use published version (default: true)

### `run_skill`
Execute a specific skill within this copilot with optional parameters.

**Parameters:**
- `skill_name` (string): The name of the skill to run
- `parameters` (object, optional): Parameters to pass to the skill

## How It Works

The installer automatically:
1. Discovers all copilots in your AnswerRocket instance
2. Creates a separate MCP server for each copilot  
3. Each server is named `answerrocket-copilot-{copilot-id}`
4. Each server's tools are specific to that copilot (no need to specify copilot ID)

**Benefits:**
- ✅ Clean namespace separation per copilot
- ✅ No need to specify copilot IDs in tool calls
- ✅ Easy to manage individual copilot servers
- ✅ Better organization for teams with multiple copilots

## Usage Examples

### Basic Question Asking
```javascript
// Using the copilot-specific MCP server (no copilot_id needed!)
await callTool('ask_question', {
  fully_contextualized_question: 'What were our top performing products last quarter?'
});
```

### Exploring Copilots
```javascript
// Get information about this copilot
const copilotInfo = await callTool('get_copilot_info');

// List available skills
console.log('Available skills:', copilotInfo.skill_ids);
```

### Running Skills
```javascript
// Run a specific skill on this copilot
await callTool('run_skill', {
  skill_name: 'Revenue Analysis',
  parameters: {
    time_period: 'last_quarter',
    breakdown: 'by_product'
  }
});
```

## Configuration

Each copilot server requires three environment variables:

- `AR_URL`: Your AnswerRocket instance URL (e.g., `https://your-instance.answerrocket.com`)
- `AR_TOKEN`: Your AnswerRocket API token
- `COPILOT_ID`: The specific copilot ID for this server

These are automatically configured during installation. The installer:
1. Discovers all copilots using the `get_copilots.py` script
2. Creates a separate server for each copilot with its unique `COPILOT_ID`
3. Names each server `answerrocket-copilot-{copilot-id}`

## Troubleshooting

### Common Issues

1. **"ERROR: No matching distribution found for mcp[cli]"**
   - This is usually due to an old pip version
   - The installer now automatically upgrades pip first
   - If you still see this error, manually run: `python -m pip install --upgrade pip`

2. **"Cannot connect to AnswerRocket"**
   - Verify your `AR_URL` is correct and accessible
   - Check that your `AR_TOKEN` is valid and not expired

3. **"Python version not supported"**
   - Ensure you have Python 3.8 or higher installed
   - Try using `python3` instead of `python`

4. **"mcp command not found"**
   - Make sure you've activated your virtual environment
   - Reinstall with `pip install "mcp[cli]"`

5. **"No copilots found"**
   - Check that your API token has the correct permissions
   - Verify you can access copilots through the AnswerRocket web interface

### Getting Help

- Check the [AnswerRocket documentation](https://docs.answerrocket.com/)
- Visit the [MCP specification](https://modelcontextprotocol.io/) for protocol details
- Open an issue on this repository for bug reports

## Development

To contribute or modify the server:

1. **Clone and install in development mode:**
   ```bash
   git clone https://github.com/answerrocket/mcp-server-demo.git
   cd mcp-server-demo
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Run the server locally:**
   ```bash
   python server.py
   ```

3. **Test with the MCP inspector:**
   ```bash
   mcp inspect server.py
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support with AnswerRocket integration, please contact [AnswerRocket support](https://answerrocket.com/support).

For MCP protocol questions, refer to the [Model Context Protocol documentation](https://modelcontextprotocol.io/).
