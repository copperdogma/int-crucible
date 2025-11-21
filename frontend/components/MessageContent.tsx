'use client';

/**
 * MessageContent component for rendering message text with proper line break handling.
 * 
 * This component ensures that:
 * - Newlines (\n) are properly rendered as line breaks
 * - Multiple consecutive newlines create paragraph breaks
 * - The text is formatted in a way that respects the AI's intended formatting
 * - Long words wrap properly without breaking layout
 * 
 * Uses a combination of CSS pre-wrap and explicit <br /> tags to ensure
 * line breaks are always rendered correctly, regardless of how the text is stored.
 */
interface MessageContentProps {
  content: string;
  className?: string;
}

export default function MessageContent({ content, className = '' }: MessageContentProps) {
  // Split by newlines and render with <br /> tags to ensure line breaks are always visible
  // This works regardless of CSS or how the text is stored
  const parts = content.split('\n');
  
  return (
    <div 
      className={`break-words ${className}`}
      style={{ 
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        overflowWrap: 'break-word'
      }}
    >
      {parts.map((part, index) => (
        <span key={index}>
          {part}
          {index < parts.length - 1 && <br />}
        </span>
      ))}
    </div>
  );
}

