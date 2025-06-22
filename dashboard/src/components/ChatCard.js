// ChatCard.js
import React from 'react';

const ChatCard = ({ chat, onClick }) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="chat-card" onClick={onClick}>
      <div className="card-header">
        <span className="project-badge">{chat.project}</span>
        <span className="platform-badge">{chat.platform}</span>
      </div>
      
      <h3 className="card-title">{chat.title}</h3>
      <p className="card-synthesis">{chat.synthesis}</p>
      
      <div className="card-tags">
        {chat.tags.slice(0, 3).map(tag => (
          <span key={tag} className="tag">{tag}</span>
        ))}
        {chat.tags.length > 3 && (
          <span className="tag-more">+{chat.tags.length - 3}</span>
        )}
      </div>
      
      <div className="card-footer">
        <span className="card-date">{formatDate(chat.created_at)}</span>
        <a 
          href={chat.source_url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="original-link"
          onClick={(e) => e.stopPropagation()}
        >
          Original →
        </a>
      </div>
    </div>
  );
};

export default ChatCard;