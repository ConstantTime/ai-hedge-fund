import { useState } from 'react';
import { Flow } from './components/Flow';
import { Opportunities } from './components/Opportunities';
import { Portfolio } from './components/Portfolio';

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
      overflow: 'auto'
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
        <div style={{ padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #dee2e6', maxHeight: '400px', overflow: 'auto' }}>
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
        <div style={{ padding: '15px', backgroundColor: '#f8d7da', border: '1px solid #f5c6cb' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#721c24' }}>❌ Error</h4>
          <p style={{ margin: 0, color: '#721c24' }}>{error}</p>
        </div>
      );
    }

    if (!apiResponse) {
      return (
        <div style={{ padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #dee2e6', maxHeight: '400px', overflow: 'auto' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#6c757d' }}>💡 Click any button above to see API response</h4>
          <p style={{ margin: 0, color: '#6c757d' }}>Real-time data will appear here</p>
        </div>
      );
    }

    return (
      <div style={{ padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #dee2e6', maxHeight: '400px', overflow: 'auto' }}>
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
        return <Portfolio />;
      case 'opportunities':
        return <Opportunities />;
      case 'agents':
        return <Flow />;
      default:
        return <Portfolio />;
    }
  };

  return (
    <div style={tabStyles.container}>
      {/* Header */}
      <div style={tabStyles.header}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>🤖 AI Hedge Fund System</h1>
        <p style={{ margin: '5px 0 0 0', color: '#6c757d' }}>
          Real-time portfolio monitoring and AI-powered opportunities
        </p>
      </div>

      {/* Tab Navigation */}
      <div style={tabStyles.tabList}>
        <TabButton value="portfolio">Portfolio Monitor</TabButton>
        <TabButton value="opportunities">AI Opportunities</TabButton>
        <TabButton value="agents">AI Agents Flow</TabButton>
      </div>

      {/* Content Area */}
      <div style={tabStyles.content}>
        {renderContent()}
      </div>
    </div>
  );
}
