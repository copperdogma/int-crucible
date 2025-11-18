'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { messagesApi, chatSessionsApi, problemSpecApi } from '@/lib/api';
import { Message } from '@/lib/api';

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
  const messagesEndRef = useRef<HTMLDivElement>(null);
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

  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!chatSessionId) throw new Error('No chat session');
      return messagesApi.create(chatSessionId, content, 'user');
    },
    onSuccess: async () => {
      // Refetch messages
      await queryClient.invalidateQueries({ queryKey: ['messages', chatSessionId] });
      
      // Trigger ProblemSpec refinement
      try {
        await problemSpecApi.refine(projectId, chatSessionId);
        // Refetch problem spec and world model
        queryClient.invalidateQueries({ queryKey: ['problemSpec', projectId] });
        queryClient.invalidateQueries({ queryKey: ['worldModel', projectId] });
      } catch (error) {
        console.error('Failed to refine problem spec:', error);
      }
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
                  {msg.role === 'user' ? 'You' : msg.role === 'agent' ? 'Agent' : 'System'}
                </div>
                <div className="whitespace-pre-wrap">{msg.content}</div>
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
      <div className="border-t bg-white p-4 chat-input-area">
        <form onSubmit={handleSend} className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
            disabled={isSending || !chatSessionId}
          />
          <button
            type="submit"
            disabled={isSending || !message.trim() || !chatSessionId}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSending ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
}

