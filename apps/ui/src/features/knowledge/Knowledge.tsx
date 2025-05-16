import React, { useState, useEffect } from 'react';
import { RetroCard } from '../../components/UI/RetroCard';
import { RetroButton } from '../../components/UI/RetroButton';
import { RetroLoader } from '../../components/UI/RetroLoader';
import { KnowledgeDetailModal } from '../../components/UI/KnowledgeDetailModal';
import { knowledgeAPI } from '../../api/knowledge';
import { useWebSocket } from '../../hooks/useWebSocket';
import type { KnowledgeItem } from '../../api/knowledge';
import type { WebSocketMessage } from '../../services/websocket';

export const Knowledge: React.FC = () => {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<KnowledgeItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [detailItem, setDetailItem] = useState<KnowledgeItem | null>(null);
  
  // WebSocket setup
  const { subscribe, unsubscribe } = useWebSocket({
    onMessage: (message: WebSocketMessage) => {
      handleWebSocketMessage(message);
    },
  });

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.event_type) {
      case 'knowledge_created':
        // Add new knowledge item to the top of the list
        const newItem: KnowledgeItem = {
          id: message.payload.id,
          title: message.payload.title,
          type: message.payload.type || 'document',
          source: message.payload.source,
          timestamp: 'Just now',
          summary: message.payload.summary || 'Processing...',
          tags: message.payload.tags || [],
          processedBy: message.payload.processedBy || 'ContentMind'
        };
        setItems(prev => [newItem, ...prev]);
        
        // Update tags if new ones are present
        if (message.payload.tags) {
          setAllTags(prev => {
            const uniqueTags = new Set([...prev, ...message.payload.tags]);
            return Array.from(uniqueTags);
          });
        }
        break;
      
      case 'knowledge_updated':
        // Update existing knowledge item
        setItems(prev => prev.map(item => 
          item.id === message.payload.id
            ? { ...item, ...message.payload }
            : item
        ));
        
        // Update selected item if it's being viewed
        if (selectedItem?.id === message.payload.id) {
          setSelectedItem(prev => prev ? { ...prev, ...message.payload } : null);
        }
        
        // Update detail item if modal is open
        if (detailItem?.id === message.payload.id) {
          setDetailItem(prev => prev ? { ...prev, ...message.payload } : null);
        }
        break;
    }
  };

  const fetchKnowledge = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: any = {};
      if (searchQuery) params.search = searchQuery;
      if (selectedTag) params.tag = selectedTag;
      
      const [itemsData, tagsData] = await Promise.all([
        knowledgeAPI.getItems(params),
        knowledgeAPI.getTags()
      ]);
      
      setItems(itemsData);
      setAllTags(tagsData);
    } catch (err) {
      console.error('Error fetching knowledge:', err);
      setError('Failed to load knowledge base');
      
      // Fallback to mock data if API fails
      const mockItems = [
        {
          id: '1',
          title: 'Q3 2024 Financial Analysis',
          type: 'document' as const,
          source: 'john@example.com',
          timestamp: '2 hours ago',
          summary: 'Quarterly financial report showing 23% revenue growth with increased operational efficiency...',
          tags: ['finance', 'quarterly-report', 'analysis'],
          processedBy: 'ContentMind'
        },
        {
          id: '2',
          title: 'Series A Pitch Deck - TechStartup Inc',
          type: 'document' as const,
          source: 'sarah@startup.com',
          timestamp: '5 hours ago',
          summary: 'AI-powered logistics platform seeking $5M Series A funding. Strong traction with 50k MAU...',
          tags: ['pitch-deck', 'series-a', 'logistics', 'ai'],
          processedBy: 'ContentMind'
        },
        {
          id: '3',
          title: 'AI Market Trends 2024',
          type: 'article' as const,
          source: 'WebFetcher',
          timestamp: '1 day ago',
          summary: 'Comprehensive analysis of AI market trends including LLM adoption, enterprise AI spend...',
          tags: ['ai', 'market-trends', 'research'],
          processedBy: 'WebFetcher'
        },
        {
          id: '4',
          title: 'Portfolio Company Update - BlueTech',
          type: 'email' as const,
          source: 'ceo@bluetech.com',
          timestamp: '2 days ago',
          summary: 'Monthly update from BlueTech showing 40% MoM growth, new enterprise customer wins...',
          tags: ['portfolio', 'update', 'saas'],
          processedBy: 'ContentMind'
        }
      ];
      setItems(mockItems);
      setAllTags(Array.from(new Set(mockItems.flatMap(item => item.tags))).sort());
    } finally {
      setLoading(false);
    }
  };

  const handleExportItem = async (id: string, format: 'json' | 'pdf' | 'md') => {
    try {
      const blob = await knowledgeAPI.exportItem(id, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `knowledge-item-${id}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting item:', err);
    }
  };

  useEffect(() => {
    fetchKnowledge();
  }, [searchQuery, selectedTag]);

  useEffect(() => {
    // Refresh every 60 seconds
    const interval = setInterval(fetchKnowledge, 60000);
    
    return () => {
      clearInterval(interval);
    };
  }, []);
  
  useEffect(() => {
    // Subscribe to WebSocket events in a separate effect
    const eventTypes = [
      'knowledge_created',
      'knowledge_updated'
    ];
    
    subscribe(eventTypes);
    
    return () => {
      unsubscribe(eventTypes);
    };
  }, [subscribe, unsubscribe]);

  const getTypeColor = (type: KnowledgeItem['type']) => {
    switch (type) {
      case 'document':
        return 'text-terminal-cyan';
      case 'article':
        return 'text-terminal-green';
      case 'email':
        return 'text-terminal-amber';
      case 'note':
        return 'text-processing-blue';
      default:
        return 'text-terminal-cyan';
    }
  };

  const filteredItems = items.filter(item => {
    const matchesSearch = searchQuery === '' || 
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.summary.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesTag = selectedTag === null || item.tags.includes(selectedTag);
    
    return matchesSearch && matchesTag;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RetroLoader text="Loading knowledge base..." size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold mb-6 text-terminal-cyan">
        KNOWLEDGE REPOSITORY
      </h2>

      {/* Search and Filters */}
      <RetroCard title="SEARCH & FILTERS">
        <div className="space-y-4">
          <div>
            <input
              type="text"
              placeholder="Search knowledge base..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 bg-terminal-dark border-2 border-terminal-cyan text-terminal-cyan placeholder-terminal-cyan/50 outline-none focus:border-terminal-cyan focus:retro-glow"
            />
          </div>
          
          <div>
            <div className="text-terminal-cyan mb-2">FILTER BY TAG:</div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedTag(null)}
                className={`px-3 py-1 border ${
                  selectedTag === null 
                    ? 'border-terminal-cyan text-terminal-cyan bg-terminal-cyan/20' 
                    : 'border-terminal-cyan/50 text-terminal-cyan/70 hover:border-terminal-cyan'
                }`}
              >
                ALL
              </button>
              {allTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => setSelectedTag(tag)}
                  className={`px-3 py-1 border ${
                    selectedTag === tag 
                      ? 'border-terminal-cyan text-terminal-cyan bg-terminal-cyan/20' 
                      : 'border-terminal-cyan/50 text-terminal-cyan/70 hover:border-terminal-cyan'
                  }`}
                >
                  {tag.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>
      </RetroCard>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Knowledge Items List */}
        <div className="lg:col-span-2">
          <RetroCard title="KNOWLEDGE ITEMS">
            <div className="space-y-3">
              {filteredItems.map((item) => (
                <div
                  key={item.id}
                  className={`p-4 border-2 border-terminal-cyan/20 hover:border-terminal-cyan cursor-pointer transition-all ${
                    selectedItem?.id === item.id ? 'bg-terminal-cyan/10' : ''
                  }`}
                  onClick={() => setSelectedItem(item)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="text-terminal-cyan font-bold flex-1">{item.title}</h4>
                    <span className="text-terminal-cyan/50 text-sm">{item.timestamp}</span>
                  </div>
                  
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`${getTypeColor(item.type)} text-sm font-bold`}>
                      [{item.type.toUpperCase()}]
                    </span>
                    <span className="text-terminal-cyan/70 text-sm">via {item.source}</span>
                  </div>
                  
                  <p className="text-terminal-cyan/80 text-sm mb-2 line-clamp-2">
                    {item.summary}
                  </p>
                  
                  <div className="flex flex-wrap gap-1">
                    {item.tags.map(tag => (
                      <span key={tag} className="text-xs px-2 py-1 border border-terminal-cyan/30 text-terminal-cyan/70">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </RetroCard>
        </div>

        {/* Item Details */}
        <div className="lg:col-span-1">
          <RetroCard title="ITEM DETAILS">
            {selectedItem ? (
              <div className="space-y-4">
                <div>
                  <span className="text-terminal-cyan/70">TITLE:</span>
                  <div className="text-terminal-cyan font-bold">{selectedItem.title}</div>
                </div>
                
                <div>
                  <span className="text-terminal-cyan/70">TYPE:</span>
                  <div className={getTypeColor(selectedItem.type)}>
                    {selectedItem.type.toUpperCase()}
                  </div>
                </div>
                
                <div>
                  <span className="text-terminal-cyan/70">SOURCE:</span>
                  <div className="text-terminal-cyan">{selectedItem.source}</div>
                </div>
                
                <div>
                  <span className="text-terminal-cyan/70">PROCESSED BY:</span>
                  <div className="text-terminal-cyan">{selectedItem.processedBy}</div>
                </div>
                
                <div>
                  <span className="text-terminal-cyan/70">SUMMARY:</span>
                  <div className="text-terminal-cyan mt-2 p-3 border border-terminal-cyan/20 max-h-40 overflow-y-auto">
                    {selectedItem.summary}
                  </div>
                </div>
                
                <div>
                  <span className="text-terminal-cyan/70">TAGS:</span>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {selectedItem.tags.map(tag => (
                      <span key={tag} className="px-2 py-1 border border-terminal-cyan text-terminal-cyan text-sm">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="flex gap-2 mt-4">
                  <RetroButton onClick={() => {
                    setDetailItem(selectedItem);
                    setShowDetailModal(true);
                  }}>
                    VIEW FULL
                  </RetroButton>
                  <RetroButton onClick={() => handleExportItem(selectedItem.id, 'json')} variant="success">
                    EXPORT JSON
                  </RetroButton>
                </div>
              </div>
            ) : (
              <div className="text-terminal-cyan/50 text-center py-8">
                Select an item to view details
              </div>
            )}
          </RetroCard>
        </div>
      </div>

      {/* Knowledge Stats */}
      <RetroCard title="REPOSITORY STATISTICS">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-terminal-cyan">
              {items.length}
            </div>
            <div className="text-terminal-cyan/70">TOTAL ITEMS</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-terminal-green">
              {items.filter(i => i.type === 'document').length}
            </div>
            <div className="text-terminal-cyan/70">DOCUMENTS</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-terminal-amber">
              {allTags.length}
            </div>
            <div className="text-terminal-cyan/70">UNIQUE TAGS</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-processing-blue">
              {new Set(items.map(i => i.processedBy)).size}
            </div>
            <div className="text-terminal-cyan/70">AGENTS USED</div>
          </div>
        </div>
      </RetroCard>

      <KnowledgeDetailModal
        item={detailItem}
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
      />
    </div>
  );
};