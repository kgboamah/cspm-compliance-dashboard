import React, { useEffect, useState } from 'react';

function App() {
  const [apiStatus, setApiStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/')
      .then(response => response.json())
      .then(data => {
        setApiStatus(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error connecting to API:', error);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{
      padding: '50px',
      textAlign: 'center',
      background: '#2F5496',
      minHeight: '100vh',
      color: 'white',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1>CSPM Compliance Dashboard</h1>
      <p style={{ fontSize: '18px', marginBottom: '30px' }}>
        Automated Multi-Framework Cloud Compliance Monitoring
      </p>
      
      {loading ? (
        <p>Connecting to backend...</p>
      ) : apiStatus ? (
        <div style={{
          background: '#27ae60',
          padding: '20px',
          borderRadius: '8px',
          marginTop: '20px',
          maxWidth: '400px',
          margin: '20px auto'
        }}>
          <h3>✅ Backend Connected</h3>
          <p>Status: {apiStatus.status}</p>
          <p>Version: {apiStatus.version}</p>
        </div>
      ) : (
        <div style={{
          background: '#e74c3c',
          padding: '20px',
          borderRadius: '8px',
          marginTop: '20px',
          maxWidth: '400px',
          margin: '20px auto'
        }}>
          <h3>❌ Backend Connection Failed</h3>
          <p>Check if backend service is running</p>
        </div>
      )}
    </div>
  );
}

export default App;