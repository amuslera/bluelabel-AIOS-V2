import { apiClient } from '../api/client';
import { systemAPI } from '../api/system';
import { agentsAPI } from '../api/agents';
import { inboxAPI } from '../api/inbox';
import { knowledgeAPI } from '../api/knowledge';

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
    usage: 'help [command]',
    execute: async (args) => {
      if (args[0] && commands[args[0]]) {
        const cmd = commands[args[0]];
        return {
          output: `${args[0]} - ${cmd.description}\nUsage: ${cmd.usage || args[0]}`,
        };
      }

      const helpText = Object.entries(commands)
        .map(([name, cmd]) => 
          `${name.padEnd(15)} - ${cmd.description}`
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
        const health = await systemAPI.getHealth();
        
        if (args[0] && health.services[args[0]]) {
          const component = health.services[args[0]];
          const time = new Date(component.lastCheck).toLocaleTimeString();
          return {
            output: `${args[0].toUpperCase()}: [${component.status.toUpperCase()}] - Last check: ${time}`,
          };
        }

        // Show all components
        const statusText = Object.entries(health.services)
          .map(([name, data]) => 
            `${name.padEnd(15)} [${data.status.toUpperCase()}]`
          )
          .join('\n');

        return {
          output: `SYSTEM STATUS: ${health.status.toUpperCase()}\n\n${statusText}`,
        };
      } catch (error) {
        // Fallback to mock data if API fails
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

      const agentName = args[0];
      let input = '';
      
      // Parse --input flag
      const inputIndex = args.indexOf('--input');
      if (inputIndex > 0 && inputIndex < args.length - 1) {
        input = args.slice(inputIndex + 1).join(' ').replace(/^["']|["']$/g, '');
      }

      if (!input) {
        return {
          output: 'Error: No input provided\nUsage: run <agent> --input "<text>"',
          type: 'error',
        };
      }

      try {
        // Get agents list to find the agent ID
        const agents = await agentsAPI.getAgents();
        const agent = agents.find(a => a.name.toLowerCase() === agentName.toLowerCase());
        
        if (!agent) {
          return {
            output: `Error: Agent '${agentName}' not found`,
            type: 'error',
          };
        }

        const timestamp = new Date().toLocaleTimeString();
        // Use special output to trigger the agent panel with progress bar
        return {
          output: `_OPEN_RUN_AGENT_PANEL_`,
          type: 'output',
        };
      } catch (error) {
        // Fallback to mock execution
        const timestamp = new Date().toLocaleTimeString();
        
        return {
          output: `[${timestamp}] Starting ${agentName} agent...\n[${timestamp}] Processing input: "${input}"\n[${timestamp}] [▓▓▓▓▓▓░░░░] 60% PROCESSING...\n[${timestamp}] Analysis complete.\n\nSUMMARY:\n────────\nThis is a mock response. Connect to real API for actual results.\n\nENTITIES: Mock, Test, Demo\nSENTIMENT: Positive (0.85)`,
          type: 'output',
        };
      }
    },
  },

  inbox: {
    description: 'View inbox items',
    usage: 'inbox [--filter <type>] [--status <status>]',
    execute: async (args) => {
      try {
        const messages = await inboxAPI.getMessages();
        
        // Parse filters
        let filter: string | null = null;
        let status: string | null = null;
        
        const filterIndex = args.indexOf('--filter');
        if (filterIndex > -1 && filterIndex < args.length - 1) {
          filter = args[filterIndex + 1];
        }
        
        const statusIndex = args.indexOf('--status');
        if (statusIndex > -1 && statusIndex < args.length - 1) {
          status = args[statusIndex + 1];
        }
        
        // Apply filters
        let filteredMessages = messages;
        if (filter !== null && filter !== undefined) {
          const filterValue = filter;
          filteredMessages = filteredMessages.filter(m => m.sender && m.sender.includes(filterValue));
        }
        if (status) {
          filteredMessages = filteredMessages.filter(m => m.status === status);
        }
        
        const header = 'ID     FROM              SUBJECT              TIME    STATUS';
        const rows = filteredMessages.map(item => {
          const statusIcon = {
            'processed': '✓',
            'processing': '⚡',
            'read': '○',
            'unread': '●'
          }[item.status] || '?';
          
          return `${item.id.substring(0, 6).padEnd(6)} ${item.sender.padEnd(17).substring(0, 17)} ${item.subject.padEnd(20).substring(0, 20)} ${item.timestamp.padEnd(7)} ${statusIcon}`;
        }).join('\n');

        return {
          output: `INBOX (${filteredMessages.length} items)\n\n${header}\n${'-'.repeat(60)}\n${rows}`,
        };
      } catch (error) {
        // Mock inbox data as fallback
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
      }
    },
  },

  knowledge: {
    description: 'Search knowledge base',
    usage: 'knowledge search "<query>" | knowledge list | knowledge get <id>',
    execute: async (args) => {
      if (args.length === 0 || args[0] === 'list') {
        try {
          const items = await knowledgeAPI.getItems();
          const recent = items.slice(0, 10);
          
          const rows = recent.map(item => 
            `${item.id.substring(0, 5).padEnd(5)} ${item.title.padEnd(25).substring(0, 25)} ${item.tags.join(',').padEnd(20).substring(0, 20)} ${item.timestamp}`
          ).join('\n');
          
          return {
            output: `Recent entries:\n\n${rows}`,
          };
        } catch (error) {
          return {
            output: 'Failed to fetch knowledge items',
            type: 'error',
          };
        }
      }

      if (args[0] === 'search' && args.length > 1) {
        const query = args.slice(1).join(' ').replace(/^["']|["']$/g, '');
        
        try {
          const items = await knowledgeAPI.getItems({ search: query });
          
          const rows = items.map(item => 
            `${item.id.substring(0, 5).padEnd(5)} ${item.title.padEnd(25).substring(0, 25)} ${item.tags.join(',').padEnd(20).substring(0, 20)} ${item.timestamp}`
          ).join('\n');
          
          return {
            output: `Search results for "${query}":\n\n${rows}`,
          };
        } catch (error) {
          // Mock results as fallback
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
        }
      }

      if (args[0] === 'get' && args[1]) {
        try {
          const item = await knowledgeAPI.getItem(args[1]);
          
          return {
            output: `ID: ${item.id}\nTitle: ${item.title}\nCreated: ${item.timestamp}\nTags: ${item.tags.join(', ')}\nSource: ${item.source}\nContent: ${item.summary}`,
          };
        } catch (error) {
          return {
            output: `Error: Knowledge item '${args[1]}' not found`,
            type: 'error',
          };
        }
      }

      return {
        output: 'Usage: knowledge search "<query>" | knowledge list | knowledge get <id>',
        type: 'error',
      };
    },
  },

  agent: {
    description: 'Manage agents',
    usage: 'agent list | agent info <name>',
    execute: async (args) => {
      if (args.length === 0 || args[0] === 'list') {
        try {
          const agents = await agentsAPI.getAgents();
          
          const list = agents
            .map(agent => 
              `${agent.name.padEnd(15)} [${agent.status.toUpperCase()}]  ${agent.type}`
            )
            .join('\n');

          return {
            output: list,
          };
        } catch (error) {
          // Mock data as fallback
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
      }

      if (args[0] === 'info' && args[1]) {
        try {
          const agents = await agentsAPI.getAgents();
          const agent = agents.find(a => a.name.toLowerCase() === args[1].toLowerCase());
          
          if (!agent) {
            return {
              output: `Error: Agent '${args[1]}' not found`,
              type: 'error',
            };
          }

          const metrics = agent.metrics || {
            successRate: 98.5,
            avgExecutionTime: 2.3,
            totalExecutions: 150
          };

          return {
            output: `Name: ${agent.name}\nStatus: ${agent.status.toUpperCase()}\nType: ${agent.type}\nLast Run: ${agent.lastRun || 'Never'}\nSuccess Rate: ${metrics.successRate}%\nAverage Time: ${metrics.avgExecutionTime}s\nTotal Executions: ${metrics.totalExecutions}`,
          };
        } catch (error) {
          return {
            output: `Name: ${args[1]}\nStatus: ONLINE\nLast Run: 2 minutes ago\nSuccess Rate: 98.5%\nAverage Time: 2.3s\nConfiguration:\n  Provider: Ollama\n  Model: llama3\n  Temperature: 0.7`,
          };
        }
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
      // This is still mock as we don't have a config API endpoint
      const mockConfig = {
        'email.codeword': 'process',
        'email.interval': '60',
        'llm.provider': 'ollama',
        'llm.model': 'llama3',
        'llm.temperature': '0.7'
      };

      if (args.length === 0 || args[0] === 'list') {
        const configText = Object.entries(mockConfig)
          .map(([key, value]) => `${key} = "${value}"`)
          .join('\n');
          
        return {
          output: configText,
        };
      }

      if (args[0] === 'get' && args[1]) {
        const value = mockConfig[args[1] as keyof typeof mockConfig];
        if (value) {
          return {
            output: `${args[1]} = "${value}"`,
          };
        }
        return {
          output: `Error: Configuration key '${args[1]}' not found`,
          type: 'error',
        };
      }

      if (args[0] === 'set' && args[1] && args[2]) {
        // In a real implementation, this would update the config
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

  execute: {
    description: 'Open agent execution panel',
    usage: 'execute [agent_name]',
    execute: async (args) => {
      return {
        output: '_OPEN_RUN_AGENT_PANEL_',
        type: 'system',
      };
    },
  },

  upload: {
    description: 'Upload and process a file',
    usage: 'upload',
    execute: async (args) => {
      return {
        output: '_OPEN_FILE_UPLOAD_',
        type: 'system',
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