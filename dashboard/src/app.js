import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [apiStatus, setApiStatus] = useState('checking...');

  useEffect(() => {
    // Test connection to FastAPI backend
    fetch('http://localhost:8000/')
      .then(response => response.json())
      .then(data => {
        setApiStatus('✅ Connected to API');
        console.log('API Response:', data);
      })
      .catch(error => {
        setApiStatus('❌ API not connected');
        console.error('API Error:', error);
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>ChatCards Dashboard</h1>
        <p>Transform AI conversations into searchable knowledge</p>
        
        <div className="status-section">
          <h3>System Status:</h3>
          <p>API Status: {apiStatus}</p>
        </div>

        <div className="coming-soon">
          <h3>Features Coming Soon:</h3>
          <ul>
            <li>Search your AI conversations</li>
            <li>View saved highlights</li>
            <li>Browse conversation library</li>
            <li>Export and share insights</li>
          </ul>
        </div>
      </header>
    </div>
  );
}

export default App;