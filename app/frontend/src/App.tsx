import { useState } from 'react';

interface ApiResponse {
  data: any;
  timestamp: string;
  endpoint: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'portfolio' | 'opportunities' | 'agents'>('portfolio');
  const [apiResponse, setApiResponse] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tabStyles = {
    container: {
      display: 'flex',
      height: '100vh',
      width: '100vw',
      flexDirection: 'column' as const,
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#ffffff',
      color: '#000000'
    },
    header: {
      padding: '20px',
      borderBottom: '1px solid #e5e5e5'
    },
    tabList: {
      display: 'flex',
      gap: '4px',
      padding: '10px 20px',
      borderBottom: '1px solid #e5e5e5',
      backgroundColor: '#f8f9fa'
    },
    tab: {
      padding: '12px 24px',
      border: 'none',
      borderRadius: '6px',
      cursor: 'pointer',
      fontWeight: '500',
      transition: 'all 0.2s'
    },
    activeTab: {
      backgroundColor: '#007bff',
      color: 'white'
    },
    inactiveTab: {
      backgroundColor: 'transparent',
      color: '#6c757d'
    },
    content: {
      flex: 1,
      padding: '20px',
      overflow: 'auto'
    },
    responseBox: {
      marginTop: '20px',
      padding: '15px',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      border: '1px solid #dee2e6',
      maxHeight: '400px',
      overflow: 'auto'
    },
    button: {
      padding: '8px 16px',
      border: 'none',
      borderRadius: '4px',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '500',
      transition: 'all 0.2s'
    }
  };

  const TabButton = ({ value, children }: { value: typeof activeTab, children: React.ReactNode }) => (
    <button
      style={{
        ...tabStyles.tab,
        ...(activeTab === value ? tabStyles.activeTab : tabStyles.inactiveTab)
      }}
      onClick={() => setActiveTab(value)}
    >
      {children}
    </button>
  );

  const handleApiCall = async (url: string, method: string = 'GET') => {
    try {
      setLoading(true);
      setError(null);
      console.log(`Making ${method} request to: ${url}`);
      
      const response = await fetch(url, { method });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log(`Response from ${url}:`, data);
      
      setApiResponse({
        data,
        timestamp: new Date().toLocaleTimeString(),
        endpoint: url
      });
      
      return data;
    } catch (error) {
      console.error(`Error calling ${url}:`, error);
      setError(`Error calling ${url}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const renderApiResponse = () => {
    if (loading) {
      return (
        <div style={tabStyles.responseBox}>
          <h4 style={{ margin: '0 0 10px 0', color: '#007bff' }}>⏳ Loading...</h4>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              border: '2px solid #f3f3f3',
              borderTop: '2px solid #007bff',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            <span>Making API request...</span>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div style={{...tabStyles.responseBox, backgroundColor: '#f8d7da', borderColor: '#f5c6cb'}}>
          <h4 style={{ margin: '0 0 10px 0', color: '#721c24' }}>❌ Error</h4>
          <p style={{ margin: 0, color: '#721c24' }}>{error}</p>
        </div>
      );
    }

    if (!apiResponse) {
      return (
        <div style={tabStyles.responseBox}>
          <h4 style={{ margin: '0 0 10px 0', color: '#6c757d' }}>💡 Click any button above to see API response</h4>
          <p style={{ margin: 0, color: '#6c757d' }}>Real-time data will appear here</p>
        </div>
      );
    }

    return (
      <div style={tabStyles.responseBox}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <h4 style={{ margin: 0, color: '#28a745' }}>✅ API Response</h4>
          <small style={{ color: '#6c757d' }}>
            {apiResponse.endpoint} • {apiResponse.timestamp}
          </small>
        </div>
        <pre style={{
          margin: 0,
          fontSize: '12px',
          lineHeight: '1.4',
          backgroundColor: '#ffffff',
          padding: '10px',
          borderRadius: '4px',
          border: '1px solid #dee2e6',
          overflow: 'auto',
          maxHeight: '300px'
        }}>
          {JSON.stringify(apiResponse.data, null, 2)}
        </pre>
      </div>
    );
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'portfolio':
        return (
          <div>
            <h2 style={{ marginBottom: '16px', color: '#28a745' }}>📊 Portfolio Monitor</h2>
            <div style={{ 
              padding: '20px', 
              backgroundColor: '#f8f9fa', 
              borderRadius: '8px',
              marginBottom: '16px'
            }}>
              <h3>Portfolio Summary</h3>
              <p>Real-time portfolio data from your Zerodha account</p>
              <div style={{ marginTop: '12px' }}>
                <button 
                  style={{
                    ...tabStyles.button,
                    backgroundColor: loading ? '#6c757d' : '#007bff',
                    color: 'white'
                  }}
                  onClick={() => handleApiCall('/portfolio/summary')}
                  disabled={loading}
                >
                  {loading ? 'Loading...' : 'Fetch Portfolio Data'}
                </button>
              </div>
            </div>
            {renderApiResponse()}
          </div>
        );
      
      case 'opportunities':
        return (
          <div>
            <h2 style={{ marginBottom: '16px', color: '#28a745' }}>🤖 AI Opportunities</h2>
            <div style={{ 
              padding: '20px', 
              backgroundColor: '#f8f9fa', 
              borderRadius: '8px',
              marginBottom: '16px'
            }}>
              <h3>Stock Screening</h3>
              <p>AI-powered stock analysis and opportunities</p>
              <div style={{ marginTop: '12px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <button 
                  style={{
                    ...tabStyles.button,
                    backgroundColor: loading ? '#6c757d' : '#28a745',
                    color: 'white'
                  }}
                  onClick={() => handleApiCall('/opportunities/status')}
                  disabled={loading}
                >
                  Check Status
                </button>
                <button 
                  style={{
                    ...tabStyles.button,
                    backgroundColor: loading ? '#6c757d' : '#17a2b8',
                    color: 'white'
                  }}
                  onClick={() => handleApiCall('/opportunities/scan?max_stocks=10')}
                  disabled={loading}
                >
                  Start Quick Scan (10 stocks)
                </button>
                <button 
                  style={{
                    ...tabStyles.button,
                    backgroundColor: loading ? '#6c757d' : '#6c757d',
                    color: 'white'
                  }}
                  onClick={() => handleApiCall('/opportunities/scan?max_stocks=20')}
                  disabled={loading}
                >
                  Start Full Scan (20 stocks)
                </button>
                <button 
                  style={{
                    ...tabStyles.button,
                    backgroundColor: loading ? '#adb5bd' : '#ffc107',
                    color: loading ? 'white' : 'black'
                  }}
                  onClick={() => handleApiCall('/opportunities/list?min_score=60&limit=10')}
                  disabled={loading}
                >
                  List Top Opportunities
                </button>
              </div>
            </div>
            {renderApiResponse()}
          </div>
        );
      
      case 'agents':
        return (
          <div>
            <h2 style={{ marginBottom: '16px', color: '#6c757d' }}>🤖 AI Agents Flow</h2>
            <div style={{ 
              padding: '20px', 
              backgroundColor: '#f8f9fa', 
              borderRadius: '8px',
              marginBottom: '16px'
            }}>
              <h3>Agent Workflow</h3>
              <p>Multi-agent system for stock analysis and trading decisions</p>
              <div style={{ marginTop: '12px' }}>
                <button 
                  style={{
                    ...tabStyles.button,
                    backgroundColor: '#6c757d',
                    color: 'white'
                  }}
                  onClick={() => console.log('Starting agent workflow...')}
                >
                  Start Workflow (Coming Soon)
                </button>
              </div>
            </div>
            <div style={tabStyles.responseBox}>
              <h4 style={{ margin: '0 0 10px 0', color: '#6c757d' }}>🚧 Under Development</h4>
              <p style={{ margin: 0, color: '#6c757d' }}>
                AI agents workflow will be integrated here to show the complete decision-making process.
              </p>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <>
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
      <div style={tabStyles.container}>
        <div style={tabStyles.header}>
          <h1 style={{ margin: 0, fontSize: '24px' }}>🎉 AI Hedge Fund System</h1>
          <p style={{ margin: '8px 0 0 0', color: '#6c757d' }}>
            Real-time portfolio monitoring and AI-powered opportunities
          </p>
        </div>
        
        <div style={tabStyles.tabList}>
          <TabButton value="portfolio">Portfolio Monitor</TabButton>
          <TabButton value="opportunities">AI Opportunities</TabButton>
          <TabButton value="agents">AI Agents Flow</TabButton>
        </div>
        
        <div style={tabStyles.content}>
          {renderContent()}
        </div>
      </div>
    </>
  );
}
