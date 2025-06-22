// App.js - Main Dashboard Component
import React, { useState, useEffect } from 'react';
import ChatCard from './components/ChatCard';
import ChatDetail from './components/ChatDetail';
import SearchBar from './components/SearchBar';
import './App.css';

function App() {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedChat, setSelectedChat] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedProject, setSelectedProject] = useState('All');

  useEffect(() => {
    fetchChats();
  }, []);

  const fetchChats = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/chats');
      if (!response.ok) throw new Error('Failed to fetch chats');
      const data = await response.json();
      setChats(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    try {
      setIsSearching(true);
      const response = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 10 })
      });
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (err) {
      console.error('Search failed:', err);
      setSearchResults([]);
    }
  };

  const handleChatClick = (chat) => {
    setSelectedChat(chat);
  };

  const handleBackToList = () => {
    setSelectedChat(null);
  };

  // Group chats by project
  const groupedChats = chats.reduce((groups, chat) => {
    const project = chat.project || 'General';
    if (!groups[project]) groups[project] = [];
    groups[project].push(chat);
    return groups;
  }, {});

  const projects = ['All', ...Object.keys(groupedChats)];
  const displayChats = isSearching ? searchResults : chats;
  const filteredChats = selectedProject === 'All' 
    ? displayChats 
    : displayChats.filter(chat => chat.project === selectedProject);

  if (loading) {
    return (
      <div className="app">
        <div className="loading">Loading your chats...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <div className="error">
          <h2>Error: {error}</h2>
          <button onClick={fetchChats} className="retry-btn">Retry</button>
        </div>
      </div>
    );
  }

  if (selectedChat) {
    return <ChatDetail chat={selectedChat} onBack={handleBackToList} />;
  }

  return (
    <div className="app">
      <header className="header">
        <h1>CIMI</h1>
        <p>Your AI conversation knowledge base</p>
      </header>

      <div className="controls">
        <SearchBar onSearch={handleSearch} />
        
        <div className="project-filter">
          <select 
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="project-select"
          >
            {projects.map(project => (
              <option key={project} value={project}>{project}</option>
            ))}
          </select>
          <span className="chat-count">({filteredChats.length} chats)</span>
        </div>
      </div>

      {isSearching && (
        <div className="search-info">
          Search results for your query ({searchResults.length} found)
        </div>
      )}

      {!isSearching && selectedProject === 'All' ? (
        // Group by project
        Object.entries(groupedChats).map(([project, projectChats]) => (
          <div key={project} className="project-section">
            <h2 className="project-title">
              {project} <span className="project-count">({projectChats.length})</span>
            </h2>
            <div className="chat-grid">
              {projectChats.map(chat => (
                <ChatCard 
                  key={chat.id} 
                  chat={chat} 
                  onClick={() => handleChatClick(chat)} 
                />
              ))}
            </div>
          </div>
        ))
      ) : (
        // Filtered view
        <div className="chat-grid">
          {filteredChats.map(chat => (
            <ChatCard 
              key={chat.id} 
              chat={chat} 
              onClick={() => handleChatClick(chat)} 
            />
          ))}
        </div>
      )}

      {filteredChats.length === 0 && (
        <div className="empty-state">
          <h3>No chats found</h3>
          <p>Use your Chrome extension or API to add chat conversations</p>
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="api-docs-link">
            View API Documentation
          </a>
        </div>
      )}
    </div>
  );
}

export default App;