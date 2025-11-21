'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatSessionsApi, ChatSession } from '@/lib/api';

interface ChatSessionSwitcherProps {
  projectId: string;
  currentChatSessionId: string | null;
  onChatSessionChange: (chatSessionId: string) => void;
}

export default function ChatSessionSwitcher({
  projectId,
  currentChatSessionId,
  onChatSessionChange,
}: ChatSessionSwitcherProps) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newChatTitle, setNewChatTitle] = useState('');
  const [newChatMode, setNewChatMode] = useState<'setup' | 'analysis'>('setup');
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const queryClient = useQueryClient();

  const { data: chatSessions = [], isLoading } = useQuery({
    queryKey: ['chatSessions', projectId],
    queryFn: () => chatSessionsApi.list(projectId),
    enabled: !!projectId,
  });

  const createChatMutation = useMutation({
    mutationFn: async () => {
      return chatSessionsApi.create(projectId, newChatTitle || undefined, newChatMode);
    },
    onSuccess: (newSession) => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions', projectId] });
      onChatSessionChange(newSession.id);
      setNewChatTitle('');
      setShowCreateForm(false);
    },
  });

  const updateChatMutation = useMutation({
    mutationFn: async ({ chatId, title }: { chatId: string; title: string }) => {
      return chatSessionsApi.update(chatId, title);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions', projectId] });
      setEditingChatId(null);
      setEditingTitle('');
    },
  });

  const handleCreateChat = (e: React.FormEvent) => {
    e.preventDefault();
    createChatMutation.mutate();
  };

  const handleStartEdit = (session: ChatSession) => {
    setEditingChatId(session.id);
    setEditingTitle(session.title || '');
  };

  const handleSaveEdit = (e: React.FormEvent, chatId: string) => {
    e.preventDefault();
    updateChatMutation.mutate({ chatId, title: editingTitle });
  };

  const handleCancelEdit = () => {
    setEditingChatId(null);
    setEditingTitle('');
  };

  const getChatDisplayName = (session: ChatSession): string => {
    if (session.title) return session.title;
    if (session.run_id) return `Analysis: Run ${session.run_id.slice(0, 8)}`;
    if (session.candidate_id) return `Analysis: Candidate ${session.candidate_id.slice(0, 8)}`;
    return session.mode === 'analysis' ? 'Analysis Chat' : 'Setup Chat';
  };

  const getChatModeBadge = (mode: string) => {
    if (mode === 'analysis') {
      return <span className="text-xs px-1.5 py-0.5 rounded bg-purple-100 text-purple-700" title="Analysis chat">📊</span>;
    }
    return <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700" title="Setup chat">💬</span>;
  };

  const getContextBadge = (session: ChatSession) => {
    if (session.run_id) {
      return (
        <span className="text-xs px-1.5 py-0.5 rounded bg-green-100 text-green-700" title={`Analysis of Run ${session.run_id}`}>
          Run {session.run_id.slice(0, 8)}
        </span>
      );
    }
    if (session.candidate_id) {
      return (
        <span className="text-xs px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-700" title={`Analysis of Candidate ${session.candidate_id}`}>
          Candidate {session.candidate_id.slice(0, 8)}
        </span>
      );
    }
    return null;
  };

  if (!projectId) {
    return null;
  }

  return (
    <div className="border-b bg-white">
      <div className="flex items-center justify-between px-4 py-2">
        <div className="flex items-center gap-2 flex-1 overflow-x-auto">
          <span className="text-sm font-medium text-gray-700 whitespace-nowrap">Chats:</span>
          {isLoading ? (
            <span className="text-sm text-gray-500">Loading...</span>
          ) : chatSessions.length === 0 ? (
            <span className="text-sm text-gray-500">No chats yet</span>
          ) : (
            <div className="flex gap-1 overflow-x-auto">
              {chatSessions.map((session) => {
                const isActive = session.id === currentChatSessionId;
                const isEditing = editingChatId === session.id;
                
                if (isEditing) {
                  return (
                    <form
                      key={session.id}
                      onSubmit={(e) => handleSaveEdit(e, session.id)}
                      className="flex items-center gap-1"
                      onClick={(e) => e.stopPropagation()}
                      onBlur={(e) => {
                        // Only cancel if the blur is not from clicking a button in the form
                        const relatedTarget = e.relatedTarget as HTMLElement;
                        if (!relatedTarget || !e.currentTarget.contains(relatedTarget)) {
                          handleCancelEdit();
                        }
                      }}
                    >
                      <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        className="px-2 py-1 text-sm border rounded text-gray-900"
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                        onKeyDown={(e) => {
                          if (e.key === 'Escape') {
                            handleCancelEdit();
                          }
                        }}
                      />
                      <button
                        type="submit"
                        className="px-1.5 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                        title="Save"
                        onMouseDown={(e) => e.preventDefault()} // Prevent blur before click
                      >
                        ✓
                      </button>
                      <button
                        type="button"
                        onClick={handleCancelEdit}
                        className="px-1.5 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                        title="Cancel"
                        onMouseDown={(e) => e.preventDefault()} // Prevent blur before click
                      >
                        ×
                      </button>
                    </form>
                  );
                }
                
                return (
                  <div
                    key={session.id}
                    className={`px-3 py-1.5 rounded text-sm whitespace-nowrap flex items-center gap-2 transition-colors ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <button
                      onClick={() => onChatSessionChange(session.id)}
                      className="flex items-center gap-2 flex-1"
                      title={session.title || `Chat ${session.id.slice(0, 8)}`}
                    >
                      <span className="truncate max-w-[120px]">{getChatDisplayName(session)}</span>
                      {getChatModeBadge(session.mode)}
                      {getContextBadge(session)}
                    </button>
                    {isActive && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStartEdit(session);
                        }}
                        className="ml-1 px-1.5 py-0.5 text-xs opacity-70 hover:opacity-100"
                        title="Edit title"
                      >
                        ✏️
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {!showCreateForm ? (
            <button
              onClick={() => setShowCreateForm(true)}
              className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 whitespace-nowrap"
            >
              + New Chat
            </button>
          ) : (
            <form onSubmit={handleCreateChat} className="flex items-center gap-2">
              <input
                type="text"
                value={newChatTitle}
                onChange={(e) => setNewChatTitle(e.target.value)}
                placeholder="Chat title (optional)"
                className="px-2 py-1 text-sm border rounded text-gray-900"
                autoFocus
              />
              <select
                value={newChatMode}
                onChange={(e) => setNewChatMode(e.target.value as 'setup' | 'analysis')}
                className="px-2 py-1 text-sm border rounded text-gray-900"
              >
                <option value="setup">Setup</option>
                <option value="analysis">Analysis</option>
              </select>
              <button
                type="submit"
                disabled={createChatMutation.isPending}
                className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap"
              >
                {createChatMutation.isPending ? 'Creating...' : 'Create'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setNewChatTitle('');
                }}
                className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 whitespace-nowrap"
              >
                Cancel
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

