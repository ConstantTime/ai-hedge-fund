import { DollarSign, PieChart, RefreshCw, TrendingDown, TrendingUp } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

interface PortfolioPosition {
  ticker: string;
  quantity: number;
  average_price: number;
  current_price: number;
  market_value: number;
  pnl: number;
  day_pnl: number;
  weight: number;
}

interface PortfolioData {
  timestamp: string;
  cash: number;
  invested_value: number;
  total_value: number;
  total_pnl: number;
  day_pnl: number;
  positions: PortfolioPosition[];
}

interface PortfolioSummary {
  timestamp: string;
  total_value: number;
  cash: number;
  invested_value: number;
  total_pnl: number;
  day_pnl: number;
  cash_percentage: number;
  position_count: number;
  top_positions: Array<{
    ticker: string;
    weight: number;
    pnl: number;
    market_value: number;
  }>;
}

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

const formatPercentage = (value: number): string => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
};

export const Portfolio: React.FC = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial portfolio summary
  const fetchSummary = async () => {
    try {
      const response = await fetch('http://localhost:8000/portfolio/summary');
      if (!response.ok) throw new Error('Failed to fetch portfolio summary');
      const data = await response.json();
      setSummary(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Refresh portfolio data
  const refreshPortfolio = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/portfolio/refresh', {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to refresh portfolio');
      await fetchSummary();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  // Setup SSE connection for real-time updates
  useEffect(() => {
    // Fetch initial summary and stop loading
    const initializeData = async () => {
      await fetchSummary();
      setIsLoading(false); // Stop loading after getting summary
    };
    
    initializeData();

    const eventSource = new EventSource('http://localhost:8000/portfolio/stream');

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'portfolio_update') {
          setPortfolioData(data.data);
        }
      } catch (err) {
        console.error('Error parsing SSE data:', err);
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      setError('Connection to portfolio stream lost');
    };

    return () => {
      eventSource.close();
    };
  }, []);

  if (isLoading && !portfolioData) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading portfolio...</span>
      </div>
    );
  }

  const currentData = portfolioData || summary;
  if (!currentData) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="text-center text-red-500">
            {error || 'Failed to load portfolio data'}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Portfolio Overview</h2>
          <p className="text-muted-foreground">
            Last updated: {new Date(currentData.timestamp).toLocaleString()}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={isConnected ? "secondary" : "destructive"}>
            {isConnected ? "Live" : "Disconnected"}
          </Badge>
          <Button onClick={refreshPortfolio} disabled={isLoading} size="sm">
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(currentData.total_value)}</div>
            {currentData.total_pnl !== undefined && (
              <p className={`text-xs ${currentData.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {currentData.total_pnl >= 0 ? <TrendingUp className="inline h-3 w-3 mr-1" /> : <TrendingDown className="inline h-3 w-3 mr-1" />}
                {formatCurrency(Math.abs(currentData.total_pnl))} total P&L
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cash Balance</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(currentData.cash)}</div>
            {'cash_percentage' in currentData && (
              <p className="text-xs text-muted-foreground">
                {currentData.cash_percentage.toFixed(1)}% of portfolio
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Invested Value</CardTitle>
            <PieChart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(currentData.invested_value)}</div>
            {'position_count' in currentData && (
              <p className="text-xs text-muted-foreground">
                {currentData.position_count} positions
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Day P&L</CardTitle>
            {currentData.day_pnl >= 0 ? <TrendingUp className="h-4 w-4 text-green-600" /> : <TrendingDown className="h-4 w-4 text-red-600" />}
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${currentData.day_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(currentData.day_pnl)}
            </div>
            <p className="text-xs text-muted-foreground">Today's change</p>
          </CardContent>
        </Card>
      </div>

      {/* Positions Table */}
      {portfolioData?.positions && portfolioData.positions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Current Positions</CardTitle>
            <CardDescription>Your active stock positions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Symbol</th>
                    <th className="text-right p-2">Quantity</th>
                    <th className="text-right p-2">Avg Price</th>
                    <th className="text-right p-2">Current Price</th>
                    <th className="text-right p-2">Market Value</th>
                    <th className="text-right p-2">P&L</th>
                    <th className="text-right p-2">Weight</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolioData.positions.map((position) => (
                    <tr key={position.ticker} className="border-b">
                      <td className="p-2 font-medium">{position.ticker}</td>
                      <td className="text-right p-2">{position.quantity}</td>
                      <td className="text-right p-2">{formatCurrency(position.average_price)}</td>
                      <td className="text-right p-2">{formatCurrency(position.current_price)}</td>
                      <td className="text-right p-2">{formatCurrency(position.market_value)}</td>
                      <td className={`text-right p-2 ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(position.pnl)}
                      </td>
                      <td className="text-right p-2">{position.weight.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top Positions */}
      {'top_positions' in currentData && currentData.top_positions && currentData.top_positions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Top Holdings</CardTitle>
            <CardDescription>Your largest positions by weight</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {currentData.top_positions.map((position, index) => (
                <div key={position.ticker} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium">{position.ticker}</p>
                      <p className="text-sm text-muted-foreground">{position.weight.toFixed(1)}% of portfolio</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{formatCurrency(position.market_value)}</p>
                    <p className={`text-sm ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(position.pnl)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card className="border-red-200">
          <CardContent className="p-4">
            <div className="text-red-600 text-sm">{error}</div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}; 