// Agent capability and execution types

export interface AgentCapability {
  inputTypes: ('text' | 'file' | 'url' | 'audio')[];
  parameters: ParameterDefinition[];
  outputFormat: OutputFormat;
  supportsStreaming: boolean;
  description?: string;
}

export interface ParameterDefinition {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'multiselect';
  label: string;
  description?: string;
  default?: any;
  required?: boolean;
  options?: { value: string; label: string }[];
  validation?: (value: any) => boolean | string;
  dependsOn?: string; // Parameter dependency
  showWhen?: (params: Record<string, any>) => boolean;
}

export interface OutputFormat {
  type: 'text' | 'json' | 'markdown' | 'structured';
  schema?: Record<string, any>;
}

export interface RunAgentRequest {
  agentId: string;
  input: AgentInput;
  parameters: Record<string, any>;
  streamOutput?: boolean;
  sessionId?: string;
}

export interface AgentInput {
  type: 'text' | 'file' | 'url' | 'audio';
  content: string | File;
  metadata?: Record<string, any>;
}

export interface AgentExecutionResult {
  success: boolean;
  output?: any;
  error?: string;
  executionTime?: number;
  metadata?: Record<string, any>;
}

export interface StreamingUpdate {
  type: 'progress' | 'partial' | 'complete' | 'error';
  data: any;
  timestamp: string;
}

// Mock agent definitions for testing
export const mockAgents: Record<string, AgentCapability> = {
  contentMind: {
    inputTypes: ['text', 'file', 'url', 'audio'],
    supportsStreaming: true,
    outputFormat: {
      type: 'structured',
      schema: {
        summary: 'string',
        entities: 'array',
        tags: 'array',
        sentiment: 'object'
      }
    },
    parameters: [
      {
        name: 'model',
        type: 'select',
        label: 'AI Model',
        description: 'Choose the AI model for processing',
        default: 'gpt-4',
        options: [
          { value: 'gpt-4', label: 'GPT-4 (Accurate)' },
          { value: 'gpt-3.5-turbo', label: 'GPT-3.5 (Fast)' },
          { value: 'claude-3', label: 'Claude 3 (Balanced)' }
        ]
      },
      {
        name: 'temperature',
        type: 'number',
        label: 'Temperature',
        description: 'Controls randomness (0-1)',
        default: 0.7,
        validation: (value) => value >= 0 && value <= 1 || 'Must be between 0 and 1'
      },
      {
        name: 'summarize',
        type: 'boolean',
        label: 'Generate Summary',
        default: true
      },
      {
        name: 'extractEntities',
        type: 'boolean',
        label: 'Extract Entities',
        default: true
      }
    ]
  },
  digestAgent: {
    inputTypes: ['text'],
    supportsStreaming: false,
    outputFormat: {
      type: 'markdown'
    },
    parameters: [
      {
        name: 'digestType',
        type: 'select',
        label: 'Digest Type',
        default: 'daily',
        options: [
          { value: 'daily', label: 'Daily Digest' },
          { value: 'weekly', label: 'Weekly Summary' },
          { value: 'custom', label: 'Custom Format' }
        ]
      },
      {
        name: 'maxLength',
        type: 'number',
        label: 'Max Length (words)',
        default: 500,
        validation: (value) => value > 0 || 'Must be positive'
      }
    ]
  }
};