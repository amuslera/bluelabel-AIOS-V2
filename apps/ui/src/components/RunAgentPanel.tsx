import React, { useState, useEffect, useRef } from 'react';
import { 
  AgentCapability, 
  RunAgentRequest, 
  AgentInput,
  StreamingUpdate,
  mockAgents,
  ParameterDefinition
} from '../types/agent';
import { useAgentExecution } from '../hooks/useAgentExecution';
import { Button } from './ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/Tabs';
import { Loader } from 'lucide-react';

interface RunAgentPanelProps {
  agentId?: string;
  onClose?: () => void;
}

export const RunAgentPanel: React.FC<RunAgentPanelProps> = ({ 
  agentId: initialAgentId,
  onClose 
}) => {
  const [selectedAgent, setSelectedAgent] = useState(initialAgentId || '');
  const [capabilities, setCapabilities] = useState<AgentCapability | null>(null);
  const [input, setInput] = useState<AgentInput>({ type: 'text', content: '' });
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [output, setOutput] = useState<any>(null);
  const [streamingUpdates, setStreamingUpdates] = useState<StreamingUpdate[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { executeAgent, streamAgent } = useAgentExecution();

  // Load agent capabilities when selected
  useEffect(() => {
    if (selectedAgent && mockAgents[selectedAgent]) {
      const caps = mockAgents[selectedAgent];
      setCapabilities(caps);
      
      // Initialize parameters with defaults
      const defaultParams: Record<string, any> = {};
      caps.parameters.forEach(param => {
        if (param.default !== undefined) {
          defaultParams[param.name] = param.default;
        }
      });
      setParameters(defaultParams);
    }
  }, [selectedAgent]);

  // Handle input changes
  const handleInputChange = (type: AgentInput['type'], content: string | File) => {
    setInput({ type, content });
  };

  // Handle parameter changes
  const handleParameterChange = (name: string, value: any) => {
    setParameters(prev => ({ ...prev, [name]: value }));
  };

  // Execute agent
  const handleExecute = async () => {
    if (!selectedAgent || !input.content) return;
    
    setIsExecuting(true);
    setOutput(null);
    setStreamingUpdates([]);
    
    const request: RunAgentRequest = {
      agentId: selectedAgent,
      input,
      parameters,
      streamOutput: capabilities?.supportsStreaming && parameters.stream !== false
    };
    
    try {
      if (request.streamOutput) {
        await streamAgent(request, (update) => {
          setStreamingUpdates(prev => [...prev, update]);
          if (update.type === 'complete') {
            setOutput(update.data);
          }
        });
      } else {
        const result = await executeAgent(request);
        setOutput(result.output);
      }
    } catch (error) {
      console.error('Agent execution failed:', error);
      setOutput({ error: error.message });
    } finally {
      setIsExecuting(false);
    }
  };

  // Render parameter control based on type
  const renderParameterControl = (param: ParameterDefinition) => {
    const value = parameters[param.name] ?? param.default;
    
    // Check if parameter should be shown
    if (param.showWhen && !param.showWhen(parameters)) {
      return null;
    }
    
    switch (param.type) {
      case 'string':
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            className="w-full p-2 bg-black border border-cyan-500 text-green-400"
            placeholder={param.description}
          />
        );
        
      case 'number':
        return (
          <input
            type="number"
            value={value || 0}
            onChange={(e) => handleParameterChange(param.name, parseFloat(e.target.value))}
            className="w-full p-2 bg-black border border-cyan-500 text-green-400"
            step="0.1"
          />
        );
        
      case 'boolean':
        return (
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={value || false}
              onChange={(e) => handleParameterChange(param.name, e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-green-400">{param.description}</span>
          </label>
        );
        
      case 'select':
        return (
          <select
            value={value || ''}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            className="w-full p-2 bg-black border border-cyan-500 text-green-400"
          >
            <option value="">Select {param.label}</option>
            {param.options?.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );
        
      default:
        return null;
    }
  };

  // Render input section based on capability
  const renderInputSection = () => {
    if (!capabilities) return null;
    
    return (
      <Tabs value={input.type} onValueChange={(type) => handleInputChange(type as any, '')}>
        <TabsList className="grid grid-cols-4 bg-black border border-cyan-500">
          {capabilities.inputTypes.includes('text') && (
            <TabsTrigger value="text" className="text-green-400">Text</TabsTrigger>
          )}
          {capabilities.inputTypes.includes('file') && (
            <TabsTrigger value="file" className="text-green-400">File</TabsTrigger>
          )}
          {capabilities.inputTypes.includes('url') && (
            <TabsTrigger value="url" className="text-green-400">URL</TabsTrigger>
          )}
          {capabilities.inputTypes.includes('audio') && (
            <TabsTrigger value="audio" className="text-green-400">Audio</TabsTrigger>
          )}
        </TabsList>
        
        <TabsContent value="text" className="mt-4">
          <textarea
            value={typeof input.content === 'string' ? input.content : ''}
            onChange={(e) => handleInputChange('text', e.target.value)}
            className="w-full h-32 p-2 bg-black border border-cyan-500 text-green-400 font-mono"
            placeholder="Enter text content..."
          />
        </TabsContent>
        
        <TabsContent value="file" className="mt-4">
          <div className="border-2 border-dashed border-cyan-500 p-8 text-center">
            <input
              ref={fileInputRef}
              type="file"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleInputChange('file', file);
              }}
              className="hidden"
              accept=".pdf,.txt,.doc,.docx"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="text-green-400 hover:text-green-300"
            >
              Click to upload or drag and drop
            </button>
            {input.type === 'file' && input.content instanceof File && (
              <p className="mt-2 text-cyan-300">{input.content.name}</p>
            )}
          </div>
        </TabsContent>
        
        <TabsContent value="url" className="mt-4">
          <input
            type="url"
            value={typeof input.content === 'string' ? input.content : ''}
            onChange={(e) => handleInputChange('url', e.target.value)}
            className="w-full p-2 bg-black border border-cyan-500 text-green-400"
            placeholder="https://example.com"
          />
        </TabsContent>
        
        <TabsContent value="audio" className="mt-4">
          <div className="border-2 border-dashed border-cyan-500 p-8 text-center">
            <input
              type="file"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleInputChange('audio', file);
              }}
              className="hidden"
              accept="audio/*"
              id="audio-upload"
            />
            <label htmlFor="audio-upload" className="text-green-400 hover:text-green-300 cursor-pointer">
              Upload audio file
            </label>
            {input.type === 'audio' && input.content instanceof File && (
              <p className="mt-2 text-cyan-300">{input.content.name}</p>
            )}
          </div>
        </TabsContent>
      </Tabs>
    );
  };

  // Render output section
  const renderOutput = () => {
    if (isExecuting) {
      return (
        <div className="flex items-center justify-center p-8">
          <Loader className="animate-spin text-cyan-500" />
          <span className="ml-2 text-green-400">Processing...</span>
        </div>
      );
    }
    
    if (streamingUpdates.length > 0) {
      return (
        <div className="space-y-2">
          {streamingUpdates.map((update, i) => (
            <div key={i} className="p-2 bg-gray-900 border border-cyan-500">
              <span className="text-cyan-300">[{update.type}]</span>
              <pre className="text-green-400 text-sm">{JSON.stringify(update.data, null, 2)}</pre>
            </div>
          ))}
        </div>
      );
    }
    
    if (output) {
      return (
        <pre className="text-green-400 p-4 bg-gray-900 border border-cyan-500 overflow-auto">
          {JSON.stringify(output, null, 2)}
        </pre>
      );
    }
    
    return null;
  };

  return (
    <div className="bg-black border border-cyan-500 p-6 font-mono">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl text-green-400">RUN AGENT</h2>
        {onClose && (
          <button onClick={onClose} className="text-red-400 hover:text-red-300">
            [X]
          </button>
        )}
      </div>
      
      {/* Agent Selection */}
      <div className="mb-6">
        <label className="block text-cyan-300 mb-2">SELECT AGENT:</label>
        <select
          value={selectedAgent}
          onChange={(e) => setSelectedAgent(e.target.value)}
          className="w-full p-2 bg-black border border-cyan-500 text-green-400"
        >
          <option value="">-- Choose Agent --</option>
          {Object.keys(mockAgents).map(agentId => (
            <option key={agentId} value={agentId}>
              {agentId.toUpperCase()}
            </option>
          ))}
        </select>
      </div>
      
      {capabilities && (
        <>
          {/* Input Section */}
          <div className="mb-6">
            <h3 className="text-cyan-300 mb-2">INPUT:</h3>
            {renderInputSection()}
          </div>
          
          {/* Parameters Section */}
          <div className="mb-6">
            <h3 className="text-cyan-300 mb-2">PARAMETERS:</h3>
            <div className="space-y-4">
              {capabilities.parameters.map(param => (
                <div key={param.name}>
                  <label className="block text-yellow-400 mb-1">
                    {param.label}
                    {param.required && <span className="text-red-400">*</span>}
                  </label>
                  {renderParameterControl(param)}
                </div>
              ))}
            </div>
          </div>
          
          {/* Execute Button */}
          <div className="mb-6">
            <Button
              onClick={handleExecute}
              disabled={isExecuting || !input.content}
              className="w-full bg-cyan-500 text-black hover:bg-cyan-400 disabled:bg-gray-700"
            >
              {isExecuting ? 'EXECUTING...' : 'EXECUTE AGENT'}
            </Button>
          </div>
          
          {/* Output Section */}
          {(output || streamingUpdates.length > 0 || isExecuting) && (
            <div>
              <h3 className="text-cyan-300 mb-2">OUTPUT:</h3>
              {renderOutput()}
            </div>
          )}
        </>
      )}
    </div>
  );
};