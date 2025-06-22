import React from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const ChatDetail = ({ chat, onBack }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'No date available';
    
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Invalid date';
      
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return 'Invalid date';
    }
  };

  const renderMarkdown = (text) => {
    if (!text) return '';
    
    // Configure marked for better spacing
    marked.setOptions({
      breaks: false,        // Don't convert single line breaks to <br>
      gfm: true,           // GitHub Flavored Markdown
      headerIds: false,    // Don't add IDs to headers
      mangle: false        // Don't mangle email addresses
    });
    
    try {
      const rawHtml = marked(text);
      return DOMPurify.sanitize(rawHtml);
    } catch (error) {
      console.error('Markdown parsing error:', error);
      return text; // Fallback to plain text
    }
  };

  return (
    <div className="chat-detail">
      <button onClick={onBack} className="back-btn">← Back to Chats</button>
      
      <div className="detail-header">
        <div className="detail-badges">
          <span className="project-badge">{chat.project}</span>
          <span className="platform-badge">{chat.platform}</span>
          <span className="ai-category-badge">{chat.project_name}</span>
        </div>
        
        <h1 className="detail-title">{chat.title}</h1>
        <p className="detail-synthesis">{chat.synthesis}</p>
        
        <div className="detail-actions">
          <a
            href={chat.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="original-btn"
          >
            View Original Chat
          </a>
          <span className="detail-date">{formatDate(chat.created_at)}</span>
        </div>
      </div>

      <div className="detail-tags">
        <h3>Tags</h3>
        <div className="tags-list">
          {chat.tags.map(tag => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      </div>

      <div className="detail-content">
        <h3>Full Recap</h3>
        <div
          className="markdown-content"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(chat.recap) }}
        />
      </div>
    </div>
  );
};

export default ChatDetail;