import React, { useState, useEffect, useRef } from 'react';
import { invoke } from '@forge/bridge';

interface Citation {
  title: string;
  url?: string;
  source_type?: string;
}

interface AnalyzeResult {
  answer: string;
  citations: Citation[];
  confidence: number;
  kb_suggestions?: Citation[];
}

interface IssueContext {
  issueKey?: string;
  issueType?: string;
  issueSummary?: string;
  issueDescription?: string;
  project?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  screenshots?: string[]; // Array of image URLs or data URLs
  result?: AnalyzeResult;
  timestamp: Date;
}

export const App: React.FC = () => {
  const [text, setText] = useState('');
  const [screenshots, setScreenshots] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [mountError, setMountError] = useState<string | null>(null);
  const [issueContext, setIssueContext] = useState<IssueContext | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load messages from Forge Storage API
  const loadMessages = async (issueKey: string): Promise<Message[]> => {
    try {
      if (typeof invoke === 'function') {
        const response = await invoke('getMessages', { issueKey }) as any;
        if (response?.ok && response?.data) {
          // Convert timestamp strings back to Date objects
          return response.data.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }));
        }
      }
    } catch (err) {
      console.warn('Failed to load messages from storage:', err);
    }
    return [];
  };

  // Save messages to Forge Storage API
  const saveMessagesToStorage = async (msgs: Message[], issueKey: string) => {
    try {
      if (typeof invoke === 'function') {
        await invoke('saveMessages', { issueKey, messages: msgs });
      }
    } catch (err) {
      console.warn('Failed to save messages to storage:', err);
    }
  };

  // Fetch issue context and load messages when component mounts
  useEffect(() => {
    async function fetchIssueContextAndMessages() {
      try {
        if (typeof invoke === 'function') {
          // Fetch issue details - context is automatically available in resolver
          const response = await invoke('getIssueContext', {}) as any;
          if (response?.ok && response?.data) {
            const context = response.data;
            setIssueContext(context);
            
            // Load messages for this issue from Forge Storage
            if (context.issueKey) {
              const savedMessages = await loadMessages(context.issueKey);
              if (savedMessages.length > 0) {
                setMessages(savedMessages);
              }
            }
          }
        }
      } catch (err) {
        console.warn('Failed to fetch issue context:', err);
      }
    }
    fetchIssueContextAndMessages();
  }, []);

  // Save messages whenever they change
  useEffect(() => {
    if (messages.length > 0 && issueContext?.issueKey) {
      saveMessagesToStorage(messages, issueContext.issueKey);
    }
  }, [messages, issueContext?.issueKey]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    const remainingSlots = 3 - screenshots.length;
    
    if (remainingSlots > 0) {
      const newScreenshots = imageFiles.slice(0, remainingSlots);
      setScreenshots([...screenshots, ...newScreenshots]);
    }
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Remove screenshot
  const removeScreenshot = (index: number) => {
    setScreenshots(screenshots.filter((_, i) => i !== index));
  };

  // Convert file to data URL for preview
  const getImagePreview = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.readAsDataURL(file);
    });
  };

  async function onSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    
    if (!text.trim() && screenshots.length === 0) {
      return;
    }

    setLoading(true);
    setError(null);

    // Save inputs before clearing
    const userInput = text.trim();
    const currentScreenshots = [...screenshots];
    
    // Clear inputs immediately
    setText('');
    setScreenshots([]);

    // Convert screenshots to preview URLs
    const screenshotPreviews = await Promise.all(
      currentScreenshots.map(file => getImagePreview(file))
    );

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userInput,
      screenshots: screenshotPreviews,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);

    try {
      // Test if @forge/bridge is available
      if (typeof invoke !== 'function') {
        throw new Error('@forge/bridge is not available. Make sure you are running in Forge environment.');
      }

      // TODO: Upload files via Forge Media API once wired; use returned ids
      const screenshotIds = currentScreenshots.length > 0 ? ['placeholder-screenshot-id'] : undefined;
      const response = await invoke('analyze', {
        queryText: userInput || undefined,
        screenshotId: screenshotIds?.[0],
        context: issueContext || {}
      } as any) as any;

      if (!response || response.ok === false) {
        throw new Error(response?.error || 'Unknown error');
      }

      const result = response.data as AnalyzeResult;

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: result.answer,
        result: result,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage = err?.message || String(err);
      setError(errorMessage);
      
      // Add error message
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${errorMessage}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
      
      // Also set mount error if it's a bridge issue
      if (errorMessage.includes('forge/bridge') || errorMessage.includes('not available')) {
        setMountError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }

  // Handle Enter key (Shift+Enter for new line, Enter to submit)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  // Auto-resize textarea
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  return (
    <div style={{ 
      fontFamily: 'Inter, system-ui, -apple-system, sans-serif', 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      backgroundColor: '#ffffff'
    }}>
      {mountError && (
        <div style={{ 
          color: '#dc2626', 
          padding: 12, 
          background: '#fef2f2', 
          margin: 12,
          borderRadius: 6,
          fontSize: 14
        }}>
          <strong>Error:</strong> {mountError}
        </div>
      )}

      {/* Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        backgroundColor: '#ffffff'
      }}>
        {messages.length === 0 && (
          <div style={{ 
            textAlign: 'center', 
            color: '#9ca3af', 
            marginTop: '40px',
            fontSize: 14
          }}>
            Start a conversation with the Ticket-Ninja to help you quickly locate the root cause
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: message.role === 'user' ? 'flex-end' : 'flex-start',
              gap: '8px'
            }}
          >
            <div
              style={{
                maxWidth: '85%',
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: message.role === 'user' ? '#3b82f6' : '#f3f4f6',
                color: message.role === 'user' ? '#ffffff' : '#1f2937',
                fontSize: 14,
                lineHeight: '1.5',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}
            >
              {message.content}
              
              {/* Screenshots in user messages */}
              {message.screenshots && message.screenshots.length > 0 && (
                <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {message.screenshots.map((preview, idx) => (
                    <img
                      key={idx}
                      src={preview}
                      alt={`Screenshot ${idx + 1}`}
                      style={{
                        maxWidth: '100%',
                        maxHeight: '200px',
                        borderRadius: '8px',
                        objectFit: 'contain'
                      }}
                    />
                  ))}
                </div>
              )}

              {/* Citations and KB suggestions in assistant messages */}
              {message.result && (
                <div style={{ marginTop: 12, fontSize: 12 }}>
                  {message.result.confidence > 0 && (
                    <div style={{ opacity: 0.8, marginBottom: 8 }}>
                      Confidence: {(message.result.confidence * 100).toFixed(0)}%
                    </div>
                  )}
                  {!!message.result.citations?.length && (
                    <div style={{ marginTop: 8 }}>
                      <strong>Citations:</strong>
                      <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                        {message.result.citations.map((c, idx) => (
                          <li key={idx} style={{ marginBottom: 4 }}>
                            {c.url ? (
                              <a href={c.url} target="_blank" rel="noopener noreferrer" 
                                 style={{ color: 'inherit', textDecoration: 'underline' }}>
                                {c.title}
                              </a>
                            ) : (
                              c.title
                            )}
                            {c.source_type && ` (${c.source_type})`}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {!!message.result.kb_suggestions?.length && (
                    <div style={{ marginTop: 8 }}>
                      <strong>KB Suggestions:</strong>
                      <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                        {message.result.kb_suggestions.map((c, idx) => (
                          <li key={idx} style={{ marginBottom: 4 }}>
                            {c.url ? (
                              <a href={c.url} target="_blank" rel="noopener noreferrer"
                                 style={{ color: 'inherit', textDecoration: 'underline' }}>
                                {c.title}
                              </a>
                            ) : (
                              c.title
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        
        {loading && (
          <div style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '8px'
          }}>
            <div
              style={{
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: '#f3f4f6',
                color: '#6b7280',
                fontSize: 14
              }}
            >
              Thinking...
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Screenshot Preview */}
      {screenshots.length > 0 && (
        <div style={{
          padding: '8px 16px',
          borderTop: '1px solid #e5e7eb',
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
          backgroundColor: '#f9fafb'
        }}>
          {screenshots.map((file, idx) => (
            <div key={idx} style={{ position: 'relative', display: 'inline-block' }}>
              <img
                src={URL.createObjectURL(file)}
                alt={`Preview ${idx + 1}`}
                style={{
                  width: '60px',
                  height: '60px',
                  objectFit: 'cover',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              />
              <button
                onClick={() => removeScreenshot(idx)}
                style={{
                  position: 'absolute',
                  top: -4,
                  right: -4,
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  border: 'none',
                  backgroundColor: '#ef4444',
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  lineHeight: 1
                }}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid #e5e7eb',
        backgroundColor: '#ffffff'
      }}>
        <div style={{
          backgroundColor: '#f9fafb',
          borderRadius: '12px',
          padding: '8px',
          border: '1px solid #e5e7eb',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          {/* Text Input */}
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type error messages or other clues, or upload screenshots that contain error messages... (Shift+Enter for new line)"
            disabled={loading}
            style={{
              width: '100%',
              minHeight: '32px',
              maxHeight: '120px',
              padding: '8px 12px',
              borderRadius: '8px',
              border: 'none',
              fontSize: 14,
              fontFamily: 'inherit',
              resize: 'none',
              outline: 'none',
              backgroundColor: 'transparent',
              color: '#1f2937',
              lineHeight: '1.5',
              overflow: 'hidden',
              boxSizing: 'border-box'
            }}
            rows={1}
          />

          {/* Buttons Row */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '8px'
          }}>
            {/* Add Screenshot Button */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={screenshots.length >= 3 || loading}
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: screenshots.length >= 3 ? '#e5e7eb' : '#3b82f6',
                color: 'white',
                cursor: screenshots.length >= 3 || loading ? 'not-allowed' : 'pointer',
                fontSize: '18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                opacity: screenshots.length >= 3 ? 0.5 : 1
              }}
              title={screenshots.length >= 3 ? 'Maximum 3 screenshots' : 'Add screenshot'}
            >
              +
            </button>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />

            {/* Submit Button */}
            <button
              type="button"
              onClick={() => onSubmit()}
              disabled={loading || (!text.trim() && screenshots.length === 0)}
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: (loading || (!text.trim() && screenshots.length === 0)) 
                  ? '#e5e7eb' 
                  : '#3b82f6',
                color: 'white',
                cursor: (loading || (!text.trim() && screenshots.length === 0)) 
                  ? 'not-allowed' 
                  : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                opacity: (loading || (!text.trim() && screenshots.length === 0)) ? 0.5 : 1
              }}
              title="Send message"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 4L8 12M4 8L8 4L12 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
