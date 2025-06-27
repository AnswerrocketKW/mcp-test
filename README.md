# AnswerRocket MCP Server

An MCP (Model Context Protocol) server that provides access to AnswerRocket's analytics and insights platform. This server allows LLM clients to interact with AnswerRocket copilots, run skills, and ask questions directly.

## Features

- 🤖 **Copilot Management**: Get information about available copilots and their capabilities
- 🛠️ **Skill Operations**: List, inspect, and run specific skills within copilots
- 💬 **Interactive Q&A**: Ask questions directly to AnswerRocket copilots and receive insights
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
5. Install all dependencies
6. Configure the MCP server with your credentials

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
   pip install answerrocket-client
   ```

4. **Get your API credentials:**
   - Go to `{YOUR_AR_URL}/apps/chat/topics?panel=user-info`
   - Click "Generate" under "Client API Key"
   - Copy the generated API key

5. **Install the MCP server:**
   ```bash
   mcp install server.py -v AR_URL="{YOUR_AR_URL}" -v AR_TOKEN="{YOUR_API_TOKEN}"
   ```

## Available Tools

### `answer_rocket_ask_question`
Ask a question to a specific AnswerRocket copilot and receive insights with visualizations.

**Parameters:**
- `copilot_id` (string): The ID of the copilot to ask
- `fully_contextualized_question` (string): Your question with full context

### `get_copilot_info`
Get detailed information about a copilot, including its available skills.

**Parameters:**
- `copilot_id` (string): The ID of the copilot
- `use_published_version` (boolean, optional): Use published version (default: true)

### `get_copilot_skill_info`
Get detailed information about a specific skill within a copilot.

**Parameters:**
- `copilot_id` (string): The ID of the copilot
- `skill_id` (string): The ID of the skill
- `use_published_version` (boolean, optional): Use published version (default: true)

### `run_copilot_skill`
Execute a specific skill with optional parameters.

**Parameters:**
- `copilot_id` (string): The ID of the copilot
- `skill_name` (string): The name of the skill to run
- `parameters` (object, optional): Parameters to pass to the skill

## Usage Examples

### Basic Question Asking
```javascript
// Using the MCP client
await callTool('answer_rocket_ask_question', {
  copilot_id: 'your-copilot-id',
  fully_contextualized_question: 'What were our top performing products last quarter?'
});
```

### Exploring Copilots
```javascript
// Get copilot information
const copilotInfo = await callTool('get_copilot_info', {
  copilot_id: 'your-copilot-id'
});

// List available skills
console.log('Available skills:', copilotInfo.skill_ids);
```

### Running Skills
```javascript
// Run a specific skill
await callTool('run_copilot_skill', {
  copilot_id: 'your-copilot-id',
  skill_name: 'Revenue Analysis',
  parameters: {
    time_period: 'last_quarter',
    breakdown: 'by_product'
  }
});
```

## Configuration

The server requires two environment variables:

- `AR_URL`: Your AnswerRocket instance URL (e.g., `https://your-instance.answerrocket.com`)
- `AR_TOKEN`: Your AnswerRocket API token

These are automatically configured during installation.

## Troubleshooting

### Common Issues

1. **"Cannot connect to AnswerRocket"**
   - Verify your `AR_URL` is correct and accessible
   - Check that your `AR_TOKEN` is valid and not expired

2. **"Python version not supported"**
   - Ensure you have Python 3.8 or higher installed
   - Try using `python3` instead of `python`

3. **"mcp command not found"**
   - Make sure you've activated your virtual environment
   - Reinstall with `pip install "mcp[cli]"`

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
