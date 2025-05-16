import React, { useState, useEffect } from 'react';
import { RetroCard } from '../../components/UI/RetroCard';
import { RetroButton } from '../../components/UI/RetroButton';
import { RetroLoader } from '../../components/UI/RetroLoader';
import { inboxAPI } from '../../api/inbox';
import { useWebSocket } from '../../hooks/useWebSocket';
import type { EmailMessage } from '../../api/inbox';
import type { WebSocketMessage } from '../../services/websocket';

export const Inbox: React.FC = () => {
  const [messages, setMessages] = useState<EmailMessage[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<EmailMessage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState<string | null>(null);
  
  // WebSocket setup
  const { subscribe, unsubscribe } = useWebSocket({
    onMessage: (message: WebSocketMessage) => {
      handleWebSocketMessage(message);
    },
  });

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.event_type) {
      case 'email_received':
        // Add new email to the top of the list
        const newEmail: EmailMessage = {
          id: message.payload.id,
          sender: message.payload.from,
          subject: message.payload.subject,
          timestamp: 'Just now',
          content: message.payload.content || '',
          status: 'unread',
          codeword: message.payload.codeword
        };
        setMessages(prev => [newEmail, ...prev]);
        break;
      
      case 'email_processed':
      case 'email_processing':
        // Update email status
        setMessages(prev => prev.map(msg => 
          msg.id === message.payload.email_id
            ? { ...msg, status: message.event_type === 'email_processed' ? 'processed' : 'processing' }
            : msg
        ));
        if (message.payload.email_id === processing) {
          setProcessing(null);
        }
        break;
    }
  };

  const fetchMessages = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await inboxAPI.getMessages();
      setMessages(data);
    } catch (err) {
      console.error('Error fetching messages:', err);
      setError('Failed to load messages');
      
      // Fallback to mock data if API fails
      setMessages([
        {
          id: '1',
          sender: 'john@example.com',
          subject: 'Q3 Report Analysis [process]',
          timestamp: '2 hours ago',
          content: 'Please analyze the attached Q3 financial report...',
          status: 'processed',
          codeword: 'process'
        },
        {
          id: '2',
          sender: 'sarah@startup.com',
          subject: 'Pitch Deck Review [process]',
          timestamp: '5 hours ago',
          content: 'Could you review our Series A pitch deck?',
          status: 'processing',
          codeword: 'process'
        },
        {
          id: '3',
          sender: 'mike@newsletter.com',
          subject: 'Weekly Tech Newsletter',
          timestamp: '1 day ago',
          content: 'This week in tech: AI developments...',
          status: 'read'
        },
        {
          id: '4',
          sender: 'team@bluelabel.ventures',
          subject: 'Monthly Portfolio Update',
          timestamp: '2 days ago',
          content: 'Portfolio companies performance metrics...',
          status: 'unread'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id: string) => {
    try {
      await inboxAPI.markAsRead(id);
      setMessages(messages.map(msg => 
        msg.id === id ? { ...msg, status: 'read' } : msg
      ));
      if (selectedMessage?.id === id) {
        setSelectedMessage({ ...selectedMessage, status: 'read' });
      }
    } catch (err) {
      console.error('Error marking as read:', err);
    }
  };

  const handleProcessMessage = async (id: string) => {
    try {
      setProcessing(id);
      await inboxAPI.processMessage(id);
      setMessages(messages.map(msg => 
        msg.id === id ? { ...msg, status: 'processing' } : msg
      ));
      if (selectedMessage?.id === id) {
        setSelectedMessage({ ...selectedMessage, status: 'processing' });
      }
    } catch (err) {
      console.error('Error processing message:', err);
    } finally {
      setProcessing(null);
    }
  };

  useEffect(() => {
    fetchMessages();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchMessages, 30000);
    
    return () => {
      clearInterval(interval);
    };
  }, []);
  
  useEffect(() => {
    // Subscribe to WebSocket events in a separate effect
    const eventTypes = [
      'email_received', 
      'email_processing',
      'email_processed'
    ];
    
    subscribe(eventTypes);
    
    return () => {
      unsubscribe(eventTypes);
    };
  }, [subscribe, unsubscribe]);

  const getStatusColor = (status: EmailMessage['status']) => {
    switch (status) {
      case 'unread':
        return 'text-terminal-cyan';
      case 'read':
        return 'text-terminal-cyan/50';
      case 'processing':
        return 'text-terminal-amber';
      case 'processed':
        return 'text-terminal-green';
      default:
        return 'text-terminal-cyan';
    }
  };

  const getStatusIndicator = (status: EmailMessage['status']) => {
    switch (status) {
      case 'unread':
        return '[NEW]';
      case 'read':
        return '[READ]';
      case 'processing':
        return '[PROCESSING]';
      case 'processed':
        return '[PROCESSED]';
      default:
        return '[UNKNOWN]';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RetroLoader text="Loading inbox..." size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold mb-6 text-terminal-cyan">
        INBOX MONITOR
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Message List */}
        <div className="lg:col-span-2">
          <RetroCard title="INCOMING MESSAGES">
            <div className="space-y-2">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`p-3 border-2 border-terminal-cyan/20 hover:border-terminal-cyan cursor-pointer transition-all ${
                    selectedMessage?.id === message.id ? 'bg-terminal-cyan/10' : ''
                  }`}
                  onClick={() => setSelectedMessage(message)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`${getStatusColor(message.status)} font-bold`}>
                          {getStatusIndicator(message.status)}
                        </span>
                        <span className="text-terminal-cyan">{message.sender}</span>
                        {message.codeword && (
                          <span className="text-terminal-amber text-sm">[{message.codeword}]</span>
                        )}
                      </div>
                      <div className="text-terminal-cyan/80 mt-1">{message.subject}</div>
                    </div>
                    <span className="text-terminal-cyan/50 text-sm">{message.timestamp}</span>
                  </div>
                </div>
              ))}
            </div>
          </RetroCard>
        </div>

        {/* Message Details */}
        <div className="lg:col-span-1">
          <RetroCard title="MESSAGE DETAILS">
            {selectedMessage ? (
              <div className="space-y-4">
                <div>
                  <span className="text-terminal-cyan/70">FROM:</span>
                  <div className="text-terminal-cyan">{selectedMessage.sender}</div>
                </div>
                <div>
                  <span className="text-terminal-cyan/70">SUBJECT:</span>
                  <div className="text-terminal-cyan">{selectedMessage.subject}</div>
                </div>
                <div>
                  <span className="text-terminal-cyan/70">STATUS:</span>
                  <div className={getStatusColor(selectedMessage.status)}>
                    {getStatusIndicator(selectedMessage.status)}
                  </div>
                </div>
                <div>
                  <span className="text-terminal-cyan/70">CONTENT:</span>
                  <div className="text-terminal-cyan mt-2 p-2 border border-terminal-cyan/20 max-h-40 overflow-y-auto">
                    {selectedMessage.content}
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  {selectedMessage.status === 'unread' && (
                    <RetroButton onClick={() => handleMarkAsRead(selectedMessage.id)}>
                      MARK READ
                    </RetroButton>
                  )}
                  {selectedMessage.codeword && selectedMessage.status !== 'processed' && (
                    <RetroButton 
                      onClick={() => handleProcessMessage(selectedMessage.id)} 
                      variant="success"
                      disabled={processing === selectedMessage.id}
                    >
                      {processing === selectedMessage.id ? 'PROCESSING...' : 'PROCESS'}
                    </RetroButton>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-terminal-cyan/50 text-center py-8">
                Select a message to view details
              </div>
            )}
          </RetroCard>
        </div>
      </div>

      {/* Inbox Stats */}
      <RetroCard title="INBOX STATISTICS">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-terminal-cyan">
              {messages.filter(m => m.status === 'unread').length}
            </div>
            <div className="text-terminal-cyan/70">UNREAD</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-terminal-amber">
              {messages.filter(m => m.status === 'processing').length}
            </div>
            <div className="text-terminal-cyan/70">PROCESSING</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-terminal-green">
              {messages.filter(m => m.status === 'processed').length}
            </div>
            <div className="text-terminal-cyan/70">PROCESSED</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-terminal-cyan">
              {messages.length}
            </div>
            <div className="text-terminal-cyan/70">TOTAL</div>
          </div>
        </div>
      </RetroCard>
    </div>
  );
};