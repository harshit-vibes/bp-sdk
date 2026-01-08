"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Bot, User, Loader2, Copy, Check, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

// Default suggestions when no conversation exists
const DEFAULT_SUGGESTIONS = [
  "What can you help me with?",
  "Show me an example",
  "Tell me about your capabilities",
];

export interface ManagerChatProps {
  /** Manager agent ID to chat with */
  managerId: string;
  /** Blueprint ID to display in header */
  blueprintId?: string;
  /** Optional initial session ID */
  sessionId?: string;
  /** Additional class names */
  className?: string;
}

/**
 * ManagerChat - Chat interface for blueprint manager agent
 *
 * Provides a simple chat UI that communicates with the manager agent
 * through the /api/builder/chat endpoint.
 */
export function ManagerChat({
  managerId,
  blueprintId,
  sessionId: initialSessionId,
  className,
}: ManagerChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(initialSessionId);
  const [copied, setCopied] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>(DEFAULT_SUGGESTIONS);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Handle copy blueprint ID
  const handleCopyId = useCallback(async () => {
    if (!blueprintId) return;
    try {
      await navigator.clipboard.writeText(blueprintId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Copy failed:", error);
    }
  }, [blueprintId]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Fetch suggestions after assistant response
  const fetchSuggestions = useCallback(async (conversationHistory: Message[]) => {
    setIsLoadingSuggestions(true);
    try {
      const response = await fetch("/api/builder/chat-suggestions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          manager_id: managerId,
          conversation: conversationHistory.map((m) => ({
            role: m.role,
            content: m.content,
          })),
          session_id: sessionId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.suggestions && data.suggestions.length > 0) {
          setSuggestions(data.suggestions);
        }
      }
    } catch (error) {
      console.error("Failed to fetch suggestions:", error);
      // Keep current suggestions on error
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, [managerId, sessionId]);

  // Handle clicking a suggestion
  const handleSuggestionClick = useCallback((suggestion: string) => {
    setInput(suggestion);
    // Focus the input
    const inputElement = document.querySelector('input[placeholder="Type a message..."]') as HTMLInputElement;
    inputElement?.focus();
  }, []);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/builder/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          manager_id: managerId,
          message: userMessage.content,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.error || errorData.detail || `Error: ${response.status}`;
        throw new Error(errorMessage);
      }

      const data = await response.json();

      // Store session ID for subsequent messages
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.response,
      };

      const newMessages = [...messages, userMessage, assistantMessage];
      setMessages(newMessages);

      // Fetch suggestions for next reply
      fetchSuggestions(newMessages);
    } catch (error) {
      console.error("Chat error:", error);
      // Add error message with details
      const errorMsg = error instanceof Error ? error.message : "Unknown error";
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `Sorry, I encountered an error: ${errorMsg}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, managerId, sessionId, messages, fetchSuggestions]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div
      className={cn(
        "flex flex-col border rounded-lg bg-background overflow-hidden",
        className
      )}
    >
      {/* Chat header */}
      <div className="flex-shrink-0 px-3 py-2 border-b bg-muted/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-orange-500" />
            <span className="text-sm font-medium">Chat Playground</span>
          </div>
          {blueprintId && (
            <button
              onClick={handleCopyId}
              className="flex items-center gap-1.5 px-2 py-1 rounded text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title="Copy Blueprint ID"
            >
              <code className="font-mono">{blueprintId.slice(0, 8)}...</code>
              {copied ? (
                <Check className="h-3 w-3 text-green-500" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-sm text-muted-foreground py-4">
            Send a message to start chatting with your blueprint&apos;s manager agent
          </div>
        )}
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex gap-2 text-sm",
              message.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            {message.role === "assistant" && (
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-100 dark:bg-orange-900 flex items-center justify-center">
                <Bot className="h-3 w-3 text-orange-600 dark:text-orange-400" />
              </div>
            )}
            <div
              className={cn(
                "max-w-[80%] rounded-lg px-3 py-2",
                message.role === "user"
                  ? "bg-orange-500 text-white"
                  : "bg-muted"
              )}
            >
              {message.role === "assistant" ? (
                <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-headings:my-2 prose-pre:my-2 prose-code:text-xs">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                      ul: ({ children }) => <ul className="mb-1 ml-4 list-disc">{children}</ul>,
                      ol: ({ children }) => <ol className="mb-1 ml-4 list-decimal">{children}</ol>,
                      li: ({ children }) => <li className="mb-0.5">{children}</li>,
                      code: ({ className, children, ...props }) => {
                        const isInline = !className;
                        return isInline ? (
                          <code className="px-1 py-0.5 rounded bg-black/10 dark:bg-white/10 text-xs font-mono" {...props}>
                            {children}
                          </code>
                        ) : (
                          <code className="block p-2 rounded bg-black/10 dark:bg-white/10 text-xs font-mono overflow-x-auto" {...props}>
                            {children}
                          </code>
                        );
                      },
                      pre: ({ children }) => <pre className="my-2 rounded overflow-hidden">{children}</pre>,
                      a: ({ href, children }) => (
                        <a href={href} target="_blank" rel="noopener noreferrer" className="text-orange-600 dark:text-orange-400 underline">
                          {children}
                        </a>
                      ),
                    }}
                  >
                    {message.content.replace(/\\n/g, '\n')}
                  </ReactMarkdown>
                </div>
              ) : (
                message.content
              )}
            </div>
            {message.role === "user" && (
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-500 flex items-center justify-center">
                <User className="h-3 w-3 text-white" />
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-2 text-sm">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-100 dark:bg-orange-900 flex items-center justify-center">
              <Bot className="h-3 w-3 text-orange-600 dark:text-orange-400" />
            </div>
            <div className="bg-muted rounded-lg px-3 py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="flex-shrink-0 p-2 border-t">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={isLoading}
            className="text-sm"
          />
          <Button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="bg-orange-500 hover:bg-orange-600"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Suggestions - below input, stacked in row */}
      {suggestions.length > 0 && !isLoading && (
        <div className="flex-shrink-0 px-2 pb-2 flex flex-row flex-wrap gap-1.5">
          {isLoadingSuggestions ? (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Loading suggestions...</span>
            </div>
          ) : (
            suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors"
              >
                <Sparkles className="h-3 w-3" />
                {suggestion}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
