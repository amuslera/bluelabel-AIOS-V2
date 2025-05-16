import { apiClient } from '../api/client';

interface CommandResult {
  output: string;
  type?: 'output' | 'error' | 'info' | 'system';
  clear?: boolean;
}

interface Command {
  description: string;
  usage?: string;
  execute: (args: string[]) => Promise<CommandResult>;
}

const commands: Record<string, Command> = {
  help: {
    description: 'Show available commands',
    execute: async () => {
      const helpText = Object.entries(commands)
        .map(([name, cmd]) => 
          `${name.padEnd(15)} - ${cmd.description}${cmd.usage ? `\n${''.padEnd(15)}   Usage: ${cmd.usage}` : ''}`
        )
        .join('\n');
      
      return {
        output: `Available commands:\n\n${helpText}\n\nFor more info on a command, type: help <command>`,
      };
    },
  },

  clear: {
    description: 'Clear the terminal',
    execute: async () => {
      return { output: '', clear: true };
    },
  },

  status: {
    description: 'Show system status',
    usage: 'status [component]',
    execute: async (args) => {
      try {
        // Mock data for now - will connect to real API later
        const mockStatus = {
          content_mind: { status: 'ok', lastCheck: '2min ago' },
          email_gateway: { status: 'ok', lastCheck: '5min ago' },
          model_router: { status: 'ok', lastCheck: '1min ago' },
          redis: { status: 'ok', lastCheck: '30sec ago' },
        };

        if (args[0] && mockStatus[args[0] as keyof typeof mockStatus]) {
          const component = mockStatus[args[0] as keyof typeof mockStatus];
          return {
            output: `${args[0].toUpperCase()}: [${component.status.toUpperCase()}] - Last check: ${component.lastCheck}`,
          };
        }

        const statusText = Object.entries(mockStatus)
          .map(([name, data]) => 
            `${name.padEnd(15)} [${data.status.toUpperCase()}]`
          )
          .join('\n');

        return {
          output: `SYSTEM STATUS: ONLINE\n\n${statusText}`,
        };
      } catch (error) {
        return {
          output: 'Failed to fetch system status',
          type: 'error',
        };
      }
    },
  },

  run: {
    description: 'Execute an agent',
    usage: 'run <agent> --input "<text>"',
    execute: async (args) => {
      if (args.length === 0) {
        return {
          output: 'Error: No agent specified\nUsage: run <agent> --input "<text>"',
          type: 'error',
        };
      }

      const agent = args[0];
      let input = '';
      
      // Parse --input flag
      const inputIndex = args.indexOf('--input');
      if (inputIndex > 0 && inputIndex < args.length - 1) {
        input = args.slice(inputIndex + 1).join(' ').replace(/^["']|["']$/g, '');
      }

      try {
        // Mock agent execution for now
        const timestamp = new Date().toLocaleTimeString();
        
        return {
          output: `[${timestamp}] Starting ${agent} agent...\n[${timestamp}] Processing input: "${input}"\n[${timestamp}] Analysis complete.\n\nSUMMARY:\n────────\nThis is a mock response. Connect to real API for actual results.\n\nENTITIES: Mock, Test, Demo\nSENTIMENT: Positive (0.85)`,
          type: 'output',
        };
      } catch (error) {
        return {
          output: `Error executing agent: ${error instanceof Error ? error.message : 'Unknown error'}`,
          type: 'error',
        };
      }
    },
  },

  inbox: {
    description: 'View inbox items',
    usage: 'inbox [--filter <type>] [--status <status>]',
    execute: async (args) => {
      try {
        // Mock inbox data for now
        const mockInbox = [
          { id: 'E042', from: 'john@example.com', subject: '[process] Q1 Report', time: '10:42', status: '✓' },
          { id: 'W041', from: '+1234567890', subject: 'Meeting request', time: '10:38', status: '✓' },
          { id: 'E040', from: 'sarah@company.com', subject: '[analyze] Budget', time: '10:30', status: '⚡' },
        ];

        const header = 'ID     FROM              SUBJECT              TIME    STATUS';
        const rows = mockInbox.map(item => 
          `${item.id.padEnd(6)} ${item.from.padEnd(17)} ${item.subject.padEnd(20)} ${item.time.padEnd(7)} ${item.status}`
        ).join('\n');

        return {
          output: `INBOX (${mockInbox.length} items)\n\n${header}\n${'-'.repeat(60)}\n${rows}`,
        };
      } catch (error) {
        return {
          output: 'Failed to fetch inbox',
          type: 'error',
        };
      }
    },
  },

  knowledge: {
    description: 'Search knowledge base',
    usage: 'knowledge search "<query>"',
    execute: async (args) => {
      if (args[0] !== 'search' || args.length < 2) {
        return {
          output: 'Usage: knowledge search "<query>"',
          type: 'error',
        };
      }

      const query = args.slice(1).join(' ').replace(/^["']|["']$/g, '');
      
      try {
        // Mock knowledge search for now
        const mockResults = [
          { id: 'K245', title: 'Q1 Financial Summary', tags: 'finance,quarterly', created: '10:42' },
          { id: 'K244', title: 'Marketing Report', tags: 'marketing,monthly', created: '09:15' },
        ];

        const results = mockResults
          .map(item => 
            `${item.id.padEnd(5)} ${item.title.padEnd(25)} ${item.tags.padEnd(20)} ${item.created}`
          )
          .join('\n');

        return {
          output: `Search results for "${query}":\n\n${results}`,
        };
      } catch (error) {
        return {
          output: 'Failed to search knowledge base',
          type: 'error',
        };
      }
    },
  },

  agent: {
    description: 'Manage agents',
    usage: 'agent list | agent info <name>',
    execute: async (args) => {
      if (args.length === 0 || args[0] === 'list') {
        // List all agents
        const mockAgents = [
          { name: 'ContentMind', status: 'ONLINE', description: 'Content analysis and summarization' },
          { name: 'WebFetcher', status: 'ONLINE', description: 'Web content extraction' },
          { name: 'DigestAgent', status: 'OFFLINE', description: 'Daily digest creation' },
        ];

        const list = mockAgents
          .map(agent => 
            `${agent.name.padEnd(15)} [${agent.status}]  ${agent.description}`
          )
          .join('\n');

        return {
          output: list,
        };
      }

      if (args[0] === 'info' && args[1]) {
        return {
          output: `Name: ${args[1]}\nStatus: ONLINE\nLast Run: 2 minutes ago\nSuccess Rate: 98.5%\nAverage Time: 2.3s\nConfiguration:\n  Provider: Ollama\n  Model: llama3\n  Temperature: 0.7`,
        };
      }

      return {
        output: 'Usage: agent list | agent info <name>',
        type: 'error',
      };
    },
  },

  config: {
    description: 'View or set configuration',
    usage: 'config list | config get <key> | config set <key> <value>',
    execute: async (args) => {
      if (args.length === 0 || args[0] === 'list') {
        return {
          output: `email.codeword = "process"\nemail.interval = 60\nllm.provider = "ollama"\nllm.model = "llama3"`,
        };
      }

      if (args[0] === 'get' && args[1]) {
        return {
          output: `${args[1]} = "value"`,
        };
      }

      if (args[0] === 'set' && args[1] && args[2]) {
        return {
          output: `[OK] ${args[1]} = "${args[2]}"`,
          type: 'info',
        };
      }

      return {
        output: 'Usage: config list | config get <key> | config set <key> <value>',
        type: 'error',
      };
    },
  },
};

export const terminalCommands = {
  execute: async (command: string, args: string[]): Promise<CommandResult> => {
    if (!command) {
      return { output: '', type: 'output' };
    }

    const cmd = commands[command.toLowerCase()];
    if (!cmd) {
      const suggestions = Object.keys(commands)
        .filter(c => c.startsWith(command.toLowerCase()))
        .slice(0, 3);
      
      return {
        output: `Command '${command}' not found${suggestions.length > 0 ? `\nDid you mean: ${suggestions.join(', ')}?` : ''}\nType "help" for available commands`,
        type: 'error',
      };
    }

    try {
      return await cmd.execute(args);
    } catch (error) {
      return {
        output: `Error executing command: ${error instanceof Error ? error.message : 'Unknown error'}`,
        type: 'error',
      };
    }
  },

  getCommands: () => Object.keys(commands),
  
  getCommandInfo: (command: string) => commands[command.toLowerCase()],
};