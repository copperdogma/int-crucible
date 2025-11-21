'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { messagesApi, chatSessionsApi, problemSpecApi, guidanceApi, projectsApi } from '@/lib/api';
import { Message, GuidanceResponse } from '@/lib/api';
import MessageContent from './MessageContent';

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
  projectId: string | null;
  chatSessionId: string | null;
  onChatSessionChange: (chatSessionId: string | null) => void;
  onProjectCreated?: (projectId: string) => void;
}

export default function ChatInterface({
  projectId,
  chatSessionId,
  onChatSessionChange,
  onProjectCreated,
}: ChatInterfaceProps) {
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isGeneratingReply, setIsGeneratingReply] = useState(false);
  const [streamingContent, setStreamingContent] = useState<string>('');
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState<{ what: string; delta?: any } | null>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  // Ref to track if we're about to start streaming (for synchronous check in query)
  const isStartingStreamRef = useRef(false);
  const lastStreamedMessageIdRef = useRef<string | null>(null);
  const prevProjectIdRef = useRef<string | null>(null);
  const [justSwitchedProject, setJustSwitchedProject] = useState(false);

  // Track if we're in project creation mode (no project yet)
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [pendingProjectDescription, setPendingProjectDescription] = useState<string | null>(null);
  const [hasCreatedProject, setHasCreatedProject] = useState(false); // Prevent duplicate creation
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null); // Show user message while creating

  // Get or create default chat session (only if project exists)
  const { data: chatSessions } = useQuery({
    queryKey: ['chatSessions', projectId],
    queryFn: () => projectId ? chatSessionsApi.list(projectId) : [],
    enabled: !!projectId,
  });

  useEffect(() => {
    // If no project, don't try to manage chat sessions
    if (!projectId) {
      return;
    }

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

  // Fetch messages for current chat session (but NOT during streaming - we use streaming pipeline only)
  // This prevents messages from "popping in" while streaming is happening
  // CRITICAL: The query is disabled during streaming to ensure we only show streaming content
  // Use ref check for synchronous evaluation (React state updates are async)
  const { data: messages = [], isLoading: messagesLoading } = useQuery({
    queryKey: ['messages', chatSessionId],
    queryFn: () => (chatSessionId ? messagesApi.list(chatSessionId) : []),
    enabled: !!chatSessionId,
    keepPreviousData: true,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Show initial greeting when no project exists
  const showInitialGreeting = !projectId && !isCreatingProject && !pendingProjectDescription;

  // Scroll to appropriate position when messages change
  useEffect(() => {
    if (justSwitchedProject) {
      messagesContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
      setJustSwitchedProject(false);
      return;
    }
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent, justSwitchedProject]);

  // Hide streaming message once saved message with delta appears
  useEffect(() => {
    if (streamingMessageId && messages.find(m => m.id === streamingMessageId)) {
      // Saved message has appeared, clear streaming state
      // The saved message will show the delta summary via DeltaSummary component
      setTimeout(() => {
        setStreamingContent('');
        setUpdatingStatus(null);
        setStreamingMessageId(null);
      }, 100);
    }
  }, [messages, streamingMessageId]);

  // Auto-focus input when chat session is ready
  useEffect(() => {
    if (chatSessionId && !messagesLoading) {
      // Small delay to ensure input is rendered
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [chatSessionId, messagesLoading]);

  // Auto-focus input when showing initial greeting (no project, first-time user)
  useEffect(() => {
    if (showInitialGreeting && !projectId) {
      // Small delay to ensure input is rendered
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [showInitialGreeting, projectId]);

  const startArchitectReplyStream = useCallback(
    async (sessionId: string, projectIdForStream: string) => {
      if (!sessionId || !projectIdForStream) {
        return;
      }

      isStartingStreamRef.current = true;
      setIsGeneratingReply(true);
      setStreamingContent('');
      setStreamingMessageId(null);
      setUpdatingStatus(null);

      try {
        await guidanceApi.generateArchitectReplyStream(
          sessionId,
          (chunk: string) => {
            setStreamingContent((prev) => prev + chunk);
          },
          async (messageId: string) => {
            setStreamingMessageId(messageId);
            isStartingStreamRef.current = false;
            setIsGeneratingReply(false);
            await queryClient.invalidateQueries({ queryKey: ['messages', sessionId] });
            await queryClient.invalidateQueries({ queryKey: ['problemSpec', projectIdForStream] });
            await queryClient.invalidateQueries({ queryKey: ['worldModel', projectIdForStream] });
            setTimeout(() => {
              inputRef.current?.focus();
            }, 100);
          },
          async (error: string) => {
            console.error('Failed to generate Architect reply:', error);
            setStreamingContent('');
            setStreamingMessageId(null);
            isStartingStreamRef.current = false;
            setIsGeneratingReply(false);
            setUpdatingStatus(null);
            await queryClient.invalidateQueries({ queryKey: ['messages', sessionId] });
            setTimeout(() => {
              inputRef.current?.focus();
            }, 100);
          },
          (what: string) => {
            setUpdatingStatus({ what });
          },
          (delta: any, what: string) => {
            setUpdatingStatus({ what, delta });
          }
        );
      } catch (error) {
        console.error('Failed to start streaming Architect reply:', error);
        isStartingStreamRef.current = false;
        setIsGeneratingReply(false);
        setStreamingContent('');
        setStreamingMessageId(null);
        try {
          await guidanceApi.generateArchitectReply(sessionId);
          await queryClient.invalidateQueries({ queryKey: ['messages', sessionId] });
        } catch (fallbackError) {
          console.error('Fallback also failed:', fallbackError);
          await queryClient.invalidateQueries({ queryKey: ['messages', sessionId] });
        }
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      }
    },
    [queryClient]
  );

  useEffect(() => {
    lastStreamedMessageIdRef.current = null;
  }, [chatSessionId]);

  useEffect(() => {
    if (!projectId) {
      prevProjectIdRef.current = null;
      return;
    }
    if (prevProjectIdRef.current === projectId) {
      return;
    }
    prevProjectIdRef.current = projectId;
    setJustSwitchedProject(true);
  }, [projectId]);

  useEffect(() => {
    if (!projectId || !chatSessionId) {
      return;
    }
    if (isGeneratingReply || isStartingStreamRef.current || messagesLoading) {
      return;
    }
    if (!messages || messages.length === 0) {
      return;
    }
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.role !== 'user') {
      return;
    }
    if (lastStreamedMessageIdRef.current === lastMessage.id) {
      return;
    }
    lastStreamedMessageIdRef.current = lastMessage.id;
    startArchitectReplyStream(chatSessionId, projectId);
  }, [
    projectId,
    chatSessionId,
    messages,
    messagesLoading,
    isGeneratingReply,
    startArchitectReplyStream,
  ]);

  // Mutation for creating project from description
  const createProjectMutation = useMutation({
    mutationFn: async (description: string) => {
      return projectsApi.createFromDescription(description);
    },
    onSuccess: async (project) => {
      // Mark that we've created a project to prevent duplicates
      setHasCreatedProject(true);
      
      // Project created - notify parent
      if (onProjectCreated) {
        onProjectCreated(project.id);
      }
      // Refresh projects list
      await queryClient.invalidateQueries({ queryKey: ['projects'] });
      
      // Get chat session immediately (it was created by backend)
      const sessions = await chatSessionsApi.list(project.id);
      if (sessions.length > 0) {
        const chatSessionId = sessions[0].id;
        onChatSessionChange(chatSessionId);
      }
      setIsCreatingProject(false);
      setPendingProjectDescription(null);
      setPendingUserMessage(null); // Clear pending message once project is created
    },
    onError: (error) => {
      console.error('Failed to create project:', error);
      setIsCreatingProject(false);
      setPendingProjectDescription(null);
      alert('Failed to create project. Please try again.');
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      // If no project, create one from the description
      if (!projectId) {
        setIsCreatingProject(true);
        setPendingProjectDescription(content);
        setPendingUserMessage(content); // Show user's message immediately
        return createProjectMutation.mutateAsync(content);
      }
      
      if (!chatSessionId) throw new Error('No chat session');
      return messagesApi.create(chatSessionId, content, 'user');
    },
    onSuccess: async (result) => {
      // If we just created a project, the mutation handler above will handle it
      if (!projectId) {
        return;
      }

      // Refetch messages
      await queryClient.invalidateQueries({ queryKey: ['messages', chatSessionId] });
      
      // Trigger ProblemSpec refinement (in background)
      problemSpecApi.refine(projectId, chatSessionId).catch((error) => {
        console.error('Failed to refine problem spec:', error);
      });
      
      // Track latest user message so auto-streaming doesn't retrigger
      if (result?.id) {
        lastStreamedMessageIdRef.current = result.id;
      }
      
      startArchitectReplyStream(chatSessionId, projectId).catch((error) => {
        console.error('Failed to stream Architect reply:', error);
      });
      
      // Note: Spec and world model queries are invalidated after streaming completes
      // (in the onDone callback) so they pick up the deltas from messages
    },
  });

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    // Prevent sending if already sending or no message
    // Allow sending even without project (will create project)
    if (!message.trim() || isSending || isCreatingProject) return;
    
    // Prevent duplicate project creation
    if (!projectId && hasCreatedProject) {
      alert('A project has already been created. Please refresh the page to create another project.');
      return;
    }
    
    // If no project and no chat session, allow sending (will create project)
    if (!projectId && !chatSessionId && message.trim()) {
      // This is fine - we'll create the project
    } else if (!projectId || (!chatSessionId && projectId)) {
      // If we have a project but no session, wait for session to be created
      return;
    }

    const messageToSend = message.trim();
    setMessage(''); // Clear input immediately so user can type next message
    setIsSending(true);
    try {
      await sendMessageMutation.mutateAsync(messageToSend);
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message. Please try again.');
      // Restore message on error
      setMessage(messageToSend);
    } finally {
      setIsSending(false);
    }
  };


  // Don't show loading screen during streaming - we're using streaming pipeline
  // Check ref synchronously (React state updates are async)
  if (messagesLoading && projectId && !isGeneratingReply && !isStartingStreamRef.current) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-gray-900">Loading messages...</div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Messages area */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Show initial greeting when no project */}
        {showInitialGreeting && (
          <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg px-4 py-2 bg-green-100 text-green-900">
              <div className="text-sm font-medium mb-1">Architect</div>
              <MessageContent content={`Hello! I'm the Architect, your AI assistant for Int Crucible.

Int Crucible is a multi-agent reasoning system that helps you solve complex problems by:
- Structuring your problem with constraints and goals
- Building a world model of your domain
- Generating and evaluating solution candidates
- Ranking them by intelligence (prediction quality / resource cost)

What are you trying to solve or make? Describe your problem, and I'll create a project for you.`} />
            </div>
          </div>
        )}

        {/* Show user's message while project is being created OR during initial streaming */}
        {/* We show this immediately so user doesn't feel their input is lost */}
        {pendingUserMessage && (isCreatingProject || (isGeneratingReply && !messages.length)) && (
          <div className="flex justify-end">
            <div className="max-w-[80%] rounded-lg px-4 py-2 bg-blue-600 text-white">
              <div className="text-sm font-medium mb-1">You</div>
              <MessageContent content={pendingUserMessage} />
            </div>
          </div>
        )}

        {/* Show creating project status only briefly, then immediately start streaming */}
        {isCreatingProject && !isGeneratingReply && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg px-4 py-2 bg-blue-100 text-blue-900">
              <div className="text-sm font-medium mb-1">System</div>
              <div>Creating your project...</div>
            </div>
          </div>
        )}

        {/* Show existing messages (even during streaming so prior context stays visible) */}
        {messages.length > 0 && (
          <>
            {messages.map((msg: Message) => (
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
                <MessageContent content={msg.content} />
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
          ))}
          </>
        )}
        
        {/* Show streaming content (ALWAYS during streaming, even if messages exist) */}
        {/* This is the ONLY rendering pipeline during streaming - no database queries interfere */}
        {(isGeneratingReply || streamingContent || updatingStatus) && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg px-4 py-2 bg-green-100 text-green-900">
              <div className="text-sm font-medium mb-1">
                {streamingContent ? 'Architect' : 'Architect is thinking...'}
              </div>
              {streamingContent ? (
                <MessageContent content={streamingContent} />
              ) : (
                <div className="flex items-center gap-1">
                  <span className="animate-pulse">●</span>
                  <span className="animate-pulse delay-75">●</span>
                  <span className="animate-pulse delay-150">●</span>
                </div>
              )}
              {/* Show updating status and delta summary */}
              {updatingStatus && (
                <div className="mt-2 pt-2 border-t border-green-200">
                  {updatingStatus.delta ? (
                    <DeltaSummary metadata={{ spec_delta: updatingStatus.delta }} />
                  ) : (
                    <div className="text-xs text-green-700">
                      Updating {updatingStatus.what}...
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
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
            placeholder={projectId ? "Type your message..." : "Describe what you're trying to solve or make..."}
            className="flex-1 px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
            disabled={isCreatingProject}
            onKeyDown={(e) => {
              // Allow Enter to send, but prevent sending while agent is replying or creating project
              if (e.key === 'Enter' && !e.shiftKey && !isSending && !isGeneratingReply && !isCreatingProject && message.trim()) {
                e.preventDefault();
                handleSend(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={isSending || isGeneratingReply || isCreatingProject || !message.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isCreatingProject ? 'Creating...' : isSending ? 'Sending...' : isGeneratingReply ? 'Architect is replying...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
}

