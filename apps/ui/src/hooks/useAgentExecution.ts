import { useState, useCallback } from 'react';
import { 
  RunAgentRequest, 
  AgentExecutionResult, 
  StreamingUpdate 
} from '../types/agent';

export const useAgentExecution = () => {
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeAgent = useCallback(async (request: RunAgentRequest): Promise<AgentExecutionResult> => {
    setIsExecuting(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/agents/${request.agentId}/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      });
      
      if (!response.ok) {
        throw new Error(`Agent execution failed: ${response.statusText}`);
      }
      
      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setIsExecuting(false);
    }
  }, []);

  const streamAgent = useCallback(async (
    request: RunAgentRequest, 
    onUpdate: (update: StreamingUpdate) => void
  ): Promise<void> => {
    setIsExecuting(true);
    setError(null);
    
    try {
      const eventSource = new EventSource(
        `/api/agents/${request.agentId}/stream?` + 
        new URLSearchParams({
          input: JSON.stringify(request.input),
          parameters: JSON.stringify(request.parameters)
        })
      );
      
      eventSource.onmessage = (event) => {
        try {
          const update: StreamingUpdate = JSON.parse(event.data);
          onUpdate(update);
          
          if (update.type === 'complete' || update.type === 'error') {
            eventSource.close();
            setIsExecuting(false);
          }
        } catch (err) {
          console.error('Failed to parse streaming update:', err);
        }
      };
      
      eventSource.onerror = (err) => {
        console.error('EventSource error:', err);
        eventSource.close();
        setIsExecuting(false);
        setError('Streaming connection failed');
        onUpdate({
          type: 'error',
          data: { error: 'Streaming connection failed' },
          timestamp: new Date().toISOString()
        });
      };
      
      // Return a cleanup function
      return new Promise((resolve) => {
        eventSource.addEventListener('close', () => {
          resolve();
        });
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      setIsExecuting(false);
      throw err;
    }
  }, []);

  // Mock execution for testing
  const mockExecuteAgent = useCallback(async (request: RunAgentRequest): Promise<AgentExecutionResult> => {
    setIsExecuting(true);
    setError(null);
    
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Return mock response based on agent
      const mockResponses: Record<string, any> = {
        contentMind: {
          summary: "This is a mock summary of the processed content.",
          entities: [
            { text: "OpenAI", type: "ORGANIZATION", confidence: 0.95 },
            { text: "AI Technology", type: "TOPIC", confidence: 0.88 }
          ],
          tags: ["artificial-intelligence", "technology", "innovation"],
          sentiment: {
            overall: "positive",
            score: 0.82
          }
        },
        digestAgent: {
          digest: "# Daily Digest\n\n## Key Points\n- Point 1\n- Point 2\n\n## Summary\nThis is a mock daily digest.",
          wordCount: 45,
          topics: ["technology", "business"]
        }
      };
      
      return {
        success: true,
        output: mockResponses[request.agentId] || { message: "Mock execution completed" },
        executionTime: 2000,
        metadata: {
          model: request.parameters.model || "default",
          timestamp: new Date().toISOString()
        }
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      return {
        success: false,
        error: errorMessage
      };
    } finally {
      setIsExecuting(false);
    }
  }, []);

  // Mock streaming for testing
  const mockStreamAgent = useCallback(async (
    request: RunAgentRequest,
    onUpdate: (update: StreamingUpdate) => void
  ): Promise<void> => {
    setIsExecuting(true);
    setError(null);
    
    try {
      // Simulate streaming updates
      const updates = [
        { type: 'progress', data: { status: 'Initializing agent...' } },
        { type: 'progress', data: { status: 'Processing input...' } },
        { type: 'partial', data: { text: 'Analyzing content...' } },
        { type: 'partial', data: { text: 'Extracting entities...' } },
        { type: 'partial', data: { text: 'Generating summary...' } },
        { type: 'complete', data: { 
          summary: 'Mock streaming complete',
          entities: ['Entity1', 'Entity2'],
          tags: ['tag1', 'tag2']
        }}
      ];
      
      for (const update of updates) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        onUpdate({
          ...update,
          timestamp: new Date().toISOString()
        } as StreamingUpdate);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      onUpdate({
        type: 'error',
        data: { error: errorMessage },
        timestamp: new Date().toISOString()
      });
    } finally {
      setIsExecuting(false);
    }
  }, []);

  return {
    executeAgent: process.env.NODE_ENV === 'development' ? mockExecuteAgent : executeAgent,
    streamAgent: process.env.NODE_ENV === 'development' ? mockStreamAgent : streamAgent,
    isExecuting,
    error
  };
};