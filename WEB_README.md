# OpenManus Web Interface

A simple web interface for OpenManus AI agents that runs on `localhost:8080`.

## Quick Start

1. **Install dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure OpenManus** (if not already done):
   ```bash
   cp config/config.example.toml config/config.toml
   # Edit config/config.toml to add your API keys
   ```

3. **Start the web server**:
   ```bash
   python run_web.py
   ```

4. **Open your browser** and go to:
   ```
   http://localhost:8080
   ```

## Features

### 🤖 Multiple Agent Types
- **OpenManus Agent**: General-purpose AI agent for various tasks
- **MCP Agent**: Model Context Protocol agent with enhanced tool support
- **Data Analysis Agent**: Specialized agent for data analysis and visualization

### 💬 Web Chat Interface
- Clean, modern chat interface
- Real-time message processing
- Session management
- Agent status indicators

### 🔧 Easy Setup
- One-command startup
- Automatic dependency checking
- Configuration validation

## How to Use

1. **Select an Agent**: Choose from the available agent types at the top
2. **Start Session**: Click "Start Session" to initialize your chosen agent
3. **Chat**: Type your messages and interact with the AI agent
4. **Switch Agents**: Select a different agent type and start a new session

## API Endpoints

The web server also provides a REST API:

- `GET /` - Web interface
- `POST /api/session/create` - Create new agent session
- `GET /api/session/{id}/status` - Get session status
- `POST /api/session/{id}/chat` - Send message to agent
- `GET /api/session/{id}/messages` - Get pending messages
- `POST /api/session/{id}/close` - Close session
- `GET /api/agents` - List available agent types
- `GET /health` - Health check

## Configuration

The web server uses the same configuration as the command-line OpenManus:

```toml
# config/config.toml
[llm]
model = "gpt-4o"
base_url = "https://api.openai.com/v1"
api_key = "sk-..."  # Your API key
max_tokens = 4096
temperature = 0.0
```

## Troubleshooting

### Port 8080 Already in Use
If port 8080 is already in use, you can modify the port in `web_server.py`:
```python
app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)  # Change to 8081
```

### Agent Not Responding
- Check that your API keys are correctly configured in `config/config.toml`
- Verify your internet connection
- Check the server logs for error messages

### Dependencies Missing
Run the installation command:
```bash
pip install flask flask-cors
```

## Development

To run in development mode with auto-reload:
```python
app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
```

## Security Note

This web interface is designed for local development and testing. For production use, consider:
- Adding authentication
- Using HTTPS
- Implementing rate limiting
- Adding input validation and sanitization
