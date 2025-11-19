'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { messagesApi, chatSessionsApi, problemSpecApi, guidanceApi } from '@/lib/api';
import { Message, GuidanceResponse } from '@/lib/api';

interface DeltaSummaryProps {
  metadata: Record<string, any>;
}

function DeltaSummary({ metadata }: DeltaSummaryProps) {
  const [showDetails, setShowDetails] = useState(false);
  
  const specDelta = metadata.spec_delta;
  const worldModelDelta = metadata.world_model_delta;
  
  // Check if deltas exist and have actual changes
  const hasSpecDelta = specDelta && (
    (specDelta.touched_sections && specDelta.touched_sections.length > 0) ||
    (specDelta.constraints && (
      (specDelta.constraints.added?.length > 0) ||
      (specDelta.constraints.updated?.length > 0) ||
      (specDelta.constraints.removed?.length > 0)
    )) ||
    (specDelta.goals && (
      (specDelta.goals.added?.length > 0) ||
      (specDelta.goals.removed?.length > 0)
    )) ||
    specDelta.resolution_changed ||
    specDelta.mode_changed
  );
  
  const hasWorldModelDelta = worldModelDelta && (
    (worldModelDelta.touched_sections && worldModelDelta.touched_sections.length > 0) ||
    (worldModelDelta.sections && Object.keys(worldModelDelta.sections).length > 0)
  );
  
  if (!hasSpecDelta && !hasWorldModelDelta) {
    return null;
  }
  
  const summaryParts: string[] = [];
  
  // Build spec summary
  if (hasSpecDelta && specDelta) {
    const specParts: string[] = [];
    const constraints = specDelta.constraints || {};
    const goals = specDelta.goals || {};
    
    const addedConstraints = (constraints.added || []).length;
    const updatedConstraints = (constraints.updated || []).length;
    const removedConstraints = (constraints.removed || []).length;
    const addedGoals = (goals.added || []).length;
    const removedGoals = (goals.removed || []).length;
    
    if (addedConstraints > 0) specParts.push(`+${addedConstraints} constraint${addedConstraints > 1 ? 's' : ''}`);
    if (updatedConstraints > 0) specParts.push(`${updatedConstraints} constraint${updatedConstraints > 1 ? 's' : ''} updated`);
    if (removedConstraints > 0) specParts.push(`-${removedConstraints} constraint${removedConstraints > 1 ? 's' : ''}`);
    if (addedGoals > 0) specParts.push(`+${addedGoals} goal${addedGoals > 1 ? 's' : ''}`);
    if (removedGoals > 0) specParts.push(`-${removedGoals} goal${removedGoals > 1 ? 's' : ''}`);
    if (specDelta.resolution_changed) specParts.push('resolution updated');
    if (specDelta.mode_changed) specParts.push('mode updated');
    
    if (specParts.length > 0) {
      summaryParts.push(`Spec update: ${specParts.join(', ')}`);
    }
  }
  
  // Build world model summary
  if (hasWorldModelDelta && worldModelDelta) {
    const modelParts: string[] = [];
    const sections = worldModelDelta.sections || {};
    
    for (const [section, changes] of Object.entries(sections)) {
      const changeData = changes as { added?: any[]; modified?: any[]; removed?: any[] };
      const added = (changeData.added || []).length;
      const modified = (changeData.modified || []).length;
      const removed = (changeData.removed || []).length;
      
      if (added > 0) modelParts.push(`+${added} ${section.slice(0, -1)}${added > 1 ? 's' : ''}`);
      if (modified > 0) modelParts.push(`${modified} ${section.slice(0, -1)}${modified > 1 ? 's' : ''} modified`);
      if (removed > 0) modelParts.push(`-${removed} ${section.slice(0, -1)}${removed > 1 ? 's' : ''}`);
    }
    
    if (modelParts.length > 0) {
      summaryParts.push(`World model update: ${modelParts.join(', ')}`);
    }
  }
  
  if (summaryParts.length === 0) {
    return null;
  }
  
  return (
    <div className="mt-2 pt-2 border-t border-green-200">
      <div className="text-xs text-green-700">
        {summaryParts.join('. ')}.
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="ml-2 text-green-600 hover:text-green-800 underline"
        >
          {showDetails ? '[Hide Details]' : '[Details]'}
        </button>
      </div>
      {showDetails && (
        <div className="mt-2 text-xs text-green-600 space-y-1">
          {specDelta && (
            <div>
              <strong>Spec changes:</strong>
              <ul className="list-disc list-inside ml-2">
                {specDelta.constraints?.added?.map((c: any, i: number) => (
                  <li key={i}>Added constraint: {c.name}</li>
                ))}
                {specDelta.constraints?.updated?.map((c: any, i: number) => (
                  <li key={i}>Updated constraint: {c.name}</li>
                ))}
                {specDelta.constraints?.removed?.map((c: any, i: number) => (
                  <li key={i}>Removed constraint: {c.name}</li>
                ))}
                {specDelta.goals?.added?.map((g: string, i: number) => (
                  <li key={i}>Added goal: {g}</li>
                ))}
                {specDelta.goals?.removed?.map((g: string, i: number) => (
                  <li key={i}>Removed goal: {g}</li>
                ))}
              </ul>
            </div>
          )}
          {worldModelDelta && (
            <div>
              <strong>World model changes:</strong>
              <ul className="list-disc list-inside ml-2">
                {Object.entries(worldModelDelta.sections || {}).map(([section, changes]) => {
                  const changeData = changes as { added?: any[]; modified?: any[]; removed?: any[] };
                  return (
                    <li key={section}>
                      {section}: {[
                        ...(changeData.added || []).map((item: any) => `+${item.name || item.id || 'item'}`),
                        ...(changeData.modified || []).map((item: any) => `~${item.name || item.id || 'item'}`),
                        ...(changeData.removed || []).map((item: any) => `-${item.name || item.id || 'item'}`)
                      ].join(', ')}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface ChatInterfaceProps {
  projectId: string;
  chatSessionId: string | null;
  onChatSessionChange: (chatSessionId: string | null) => void;
}

export default function ChatInterface({
  projectId,
  chatSessionId,
  onChatSessionChange,
}: ChatInterfaceProps) {
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isGeneratingReply, setIsGeneratingReply] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Get or create default chat session
  const { data: chatSessions } = useQuery({
    queryKey: ['chatSessions', projectId],
    queryFn: () => chatSessionsApi.list(projectId),
  });

  useEffect(() => {
    // Reset when project changes
    if (chatSessionId) {
      // Check if the current chat session belongs to this project
      const currentSession = chatSessions?.find(s => s.id === chatSessionId);
      if (currentSession && currentSession.project_id !== projectId) {
        // Chat session belongs to a different project, reset it
        onChatSessionChange(null);
        return;
      }
    }
    
    // Get or create default chat session for this project
    if (!chatSessionId && chatSessions && chatSessions.length > 0) {
      // Use the first chat session for this project
      const projectSession = chatSessions.find(s => s.project_id === projectId);
      if (projectSession) {
        onChatSessionChange(projectSession.id);
      } else {
        // No session for this project yet, create one
        chatSessionsApi.create(projectId, 'Main Chat', 'setup').then((session) => {
          onChatSessionChange(session.id);
        });
      }
    } else if (!chatSessionId && chatSessions && chatSessions.length === 0) {
      // Create a new chat session
      chatSessionsApi.create(projectId, 'Main Chat', 'setup').then((session) => {
        onChatSessionChange(session.id);
      });
    }
  }, [chatSessionId, chatSessions, projectId, onChatSessionChange]);

  // Fetch messages for current chat session
  const { data: messages = [], isLoading: messagesLoading } = useQuery({
    queryKey: ['messages', chatSessionId],
    queryFn: () => (chatSessionId ? messagesApi.list(chatSessionId) : []),
    enabled: !!chatSessionId,
  });

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-focus input when chat session is ready
  useEffect(() => {
    if (chatSessionId && !messagesLoading) {
      // Small delay to ensure input is rendered
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [chatSessionId, messagesLoading]);

  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!chatSessionId) throw new Error('No chat session');
      return messagesApi.create(chatSessionId, content, 'user');
    },
    onSuccess: async () => {
      // Refetch messages
      await queryClient.invalidateQueries({ queryKey: ['messages', chatSessionId] });
      
      // Trigger ProblemSpec refinement (in background)
      problemSpecApi.refine(projectId, chatSessionId).catch((error) => {
        console.error('Failed to refine problem spec:', error);
      });
      
      // Automatically generate Architect reply
      setIsGeneratingReply(true);
      try {
        await guidanceApi.generateArchitectReply(chatSessionId);
        // Refetch messages to show the Architect reply
        await queryClient.invalidateQueries({ queryKey: ['messages', chatSessionId] });
      } catch (error) {
        console.error('Failed to generate Architect reply:', error);
        // Error handling is done on the backend - it creates a system message
        // Just refetch to show any system error messages
        await queryClient.invalidateQueries({ queryKey: ['messages', chatSessionId] });
      } finally {
        setIsGeneratingReply(false);
        // Refocus input after Architect reply completes
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      }
      
      // Refetch problem spec and world model (may have been updated)
      queryClient.invalidateQueries({ queryKey: ['problemSpec', projectId] });
      queryClient.invalidateQueries({ queryKey: ['worldModel', projectId] });
    },
  });

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isSending || !chatSessionId) return;

    setIsSending(true);
    try {
      await sendMessageMutation.mutateAsync(message.trim());
      setMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message. Please try again.');
    } finally {
      setIsSending(false);
    }
  };


  if (messagesLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-gray-900">Loading messages...</div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-700 mt-8">
            Start a conversation by describing your problem...
          </div>
        ) : (
          messages.map((msg: Message) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : msg.role === 'agent'
                    ? 'bg-green-100 text-green-900'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="text-sm font-medium mb-1">
                  {msg.role === 'user' 
                    ? 'You' 
                    : msg.role === 'agent' 
                    ? (msg.message_metadata?.agent_name || 'Architect')
                    : 'System'}
                </div>
                <div className="whitespace-pre-wrap">{msg.content}</div>
                {msg.role === 'agent' && msg.message_metadata && (
                  <DeltaSummary metadata={msg.message_metadata} />
                )}
                {msg.created_at && (
                  <div className="text-xs opacity-70 mt-1">
                    {(() => {
                      // Parse date - ensure proper timezone handling
                      const dateStr = msg.created_at;
                      let date: Date;
                      
                      // Check if date string has timezone info
                      // ISO format with timezone: "2025-01-17T23:28:00Z" or "2025-01-17T23:28:00+00:00"
                      // ISO format without timezone: "2025-01-17T23:28:00"
                      if (dateStr.includes('Z') || dateStr.match(/[+-]\d{2}:\d{2}$/)) {
                        // Has timezone info, parse directly
                        date = new Date(dateStr);
                      } else {
                        // No timezone info - Python's isoformat() without timezone
                        // Treat as UTC and let JavaScript convert to local
                        date = new Date(dateStr + 'Z');
                      }
                      
                      return date.toLocaleTimeString(undefined, {
                        hour: 'numeric',
                        minute: '2-digit',
                        hour12: true,
                      });
                    })()}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t bg-white p-4 chat-input-area flex-shrink-0">
        <form onSubmit={handleSend} className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
            disabled={isSending || !chatSessionId}
          />
          <button
            type="submit"
            disabled={isSending || isGeneratingReply || !message.trim() || !chatSessionId}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSending ? 'Sending...' : isGeneratingReply ? 'Architect is replying...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
}

