// SearchBar.js
import React, { useState, useEffect } from 'react';

const SearchBar = ({ onSearch }) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      onSearch(query);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [query, onSearch]);

  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="Search your chats..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="search-input"
      />
    </div>
  );
};

export default SearchBar;