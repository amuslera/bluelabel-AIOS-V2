# Terminal Commands Reference

The Bluelabel AIOS terminal provides a comprehensive command-line interface for interacting with the AI agent system. This document details all available commands, their syntax, and usage examples.

## Command Syntax

All commands follow the pattern:
```
<command> [subcommand] [arguments] [--options]
```

## Available Commands

### System Commands

#### `help`
Show available commands and their descriptions.

**Usage:**
```bash
help                    # List all commands
help <command>          # Get detailed help for a specific command
```

**Example:**
```bash
> help
Available commands:

clear           - Clear the terminal
status          - Show system status
...

> help status
Show system status
Usage: status [component]
```

#### `clear`
Clear the terminal output.

**Usage:**
```bash
clear
```

**Example:**
```bash
> clear
# Terminal is cleared
```

#### `status`
Display system and component status.

**Usage:**
```bash
status                  # Show overall system status
status <component>      # Show specific component status
```

**Available Components:**
- `content_mind` - Content analysis agent
- `email_gateway` - Email integration service
- `model_router` - LLM routing service
- `redis` - Message queue

**Example:**
```bash
> status
SYSTEM STATUS: ONLINE

content_mind    [OK]
email_gateway   [OK]
model_router    [OK]
redis          [OK]

> status content_mind
CONTENT_MIND: [OK] - Last check: 2min ago
```

### Agent Commands

#### `run`
Execute an agent with specified input.

**Usage:**
```bash
run <agent> --input "<text>"
```

**Available Agents:**
- `ContentMind` - Content analysis and summarization
- `WebFetcher` - Web content extraction
- `DigestAgent` - Daily digest creation

**Example:**
```bash
> run ContentMind --input "Analyze this quarterly report"
[10:42:15] Starting ContentMind agent...
[10:42:15] Processing input: "Analyze this quarterly report"
[10:42:17] Analysis complete.

SUMMARY:
────────
Key findings from quarterly report...

ENTITIES: Finance, Q4, Revenue
SENTIMENT: Positive (0.85)
```

#### `agent`
Manage and monitor agents.

**Usage:**
```bash
agent list              # List all agents
agent info <n>        # Show detailed info for an agent
```

**Example:**
```bash
> agent list
ContentMind     [ONLINE]  Content analysis and summarization
WebFetcher      [ONLINE]  Web content extraction
DigestAgent     [OFFLINE] Daily digest creation

> agent info ContentMind
Name: ContentMind
Status: ONLINE
Last Run: 2 minutes ago
Success Rate: 98.5%
Average Time: 2.3s
Configuration:
  Provider: Ollama
  Model: llama3
  Temperature: 0.7
```

### Communication Commands

#### `inbox`
View and manage inbox items from email and WhatsApp.

**Usage:**
```bash
inbox                           # List all inbox items
inbox --filter <type>           # Filter by source type
inbox --status <status>         # Filter by status
```

**Filter Options:**
- `--filter email` - Show only emails
- `--filter whatsapp` - Show only WhatsApp messages
- `--status processed` - Show processed items
- `--status pending` - Show pending items

**Example:**
```bash
> inbox
INBOX (3 items)

ID     FROM              SUBJECT              TIME    STATUS
------------------------------------------------------------
E042   john@example.com  [process] Q1 Report  10:42   ✓
W041   +1234567890      Meeting request      10:38   ✓
E040   sarah@company.com [analyze] Budget     10:30   ⚡

> inbox --filter email --status pending
INBOX (1 item)

ID     FROM              SUBJECT              TIME    STATUS
------------------------------------------------------------
E040   sarah@company.com [analyze] Budget     10:30   ⚡
```

### Knowledge Base Commands

#### `knowledge`
Search and manage the knowledge repository.

**Usage:**
```bash
knowledge search "<query>"      # Search knowledge base
knowledge list                  # List recent entries
knowledge get <id>             # Retrieve specific entry
```

**Example:**
```bash
> knowledge search "quarterly earnings"
Search results for "quarterly earnings":

K245  Q1 Financial Summary      finance,quarterly    10:42
K244  Earnings Call Notes       finance,calls       09:15
K242  Market Analysis Q1        finance,market      08:30

> knowledge get K245
ID: K245
Title: Q1 Financial Summary
Created: 2024-01-15 10:42
Tags: finance, quarterly
Source: email
Content: [Full document content...]
```

### Configuration Commands

#### `config`
View and modify system configuration.

**Usage:**
```bash
config list                     # List all settings
config get <key>               # Get specific setting
config set <key> <value>       # Update a setting
```

**Available Settings:**
- `email.codeword` - Keyword to trigger processing
- `email.interval` - Check interval in seconds
- `llm.provider` - LLM provider (openai, ollama, etc.)
- `llm.model` - Model name
- `llm.temperature` - Generation temperature

**Example:**
```bash
> config list
email.codeword = "process"
email.interval = 60
llm.provider = "ollama"
llm.model = "llama3"

> config get llm.model
llm.model = "llama3"

> config set llm.temperature 0.8
[OK] llm.temperature = "0.8"
```

## Command Options

### Global Options
- `--help` - Show help for any command
- `--verbose` - Enable verbose output
- `--json` - Return output in JSON format

### Output Types
Commands return different types of output:
- `output` - Normal command output (green)
- `error` - Error messages (red)
- `info` - Informational messages (cyan)
- `system` - System messages (yellow)
- `command` - Echoed commands (white)

## Command History

The terminal maintains a command history that can be navigated using:
- **Up Arrow** - Previous command
- **Down Arrow** - Next command
- **Ctrl+R** - Search command history (planned)

## Auto-completion

Tab completion is available for:
- Command names
- Agent names
- Configuration keys
- File paths (planned)

## Aliases (Planned)

Create custom command shortcuts:
```bash
alias ll="inbox --filter email"
alias ca="run ContentMind --input"
```

## Batch Processing (Planned)

Execute multiple commands from a file:
```bash
exec batch_process.txt
```

## Examples

### Common Workflows

**Process an email:**
```bash
> inbox
> run ContentMind --input "E042"
> knowledge search "Q1 Report"
```

**Check system health:**
```bash
> status
> agent list
> config list
```

**Configure agent:**
```bash
> agent info ContentMind
> config set llm.model "gpt-4"
> run ContentMind --input "test"
```

## Error Messages

Common error messages and solutions:

- `Command 'xyz' not found` - Check spelling or use `help`
- `Error: No agent specified` - Provide agent name
- `Agent not available` - Check agent status with `agent list`
- `Connection error` - Check system status with `status`

## Tips and Tricks

1. Use quotes for multi-word arguments
2. Chain commands with `&&` (planned)
3. Use `clear` to reset cluttered terminal
4. Check `help <command>` for detailed usage
5. Monitor real-time logs in separate tab

---

Last Updated: January 2025
Version: 1.0.0