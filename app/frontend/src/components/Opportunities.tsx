import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle, Loader2, Shield, Target, TrendingDown, TrendingUp } from 'lucide-react';
import React, { useEffect, useState } from 'react';

interface StockOpportunity {
  ticker: string;
  company_name: string;
  current_price: number;
  market_cap: number;
  sector: string;
  technical_indicators: {
    rsi: number;
    macd_signal: string;
    moving_avg_trend: string;
    volume_surge: boolean;
  };
  fundamental_metrics: {
    pe_ratio: number;
    debt_to_equity: number;
    roe: number;
    revenue_growth: number;
  };
  ai_analysis: {
    technical_score: number;
    fundamental_score: number;
    overall_score: number;
    signal: string;
    confidence: number;
    target_price: number;
    stop_loss: number;
  };
  reasoning: {
    buy_reasons: string[];
    risk_factors: string[];
  };
}

interface ScanStatus {
  scan_in_progress: boolean;
  opportunities_cached: number;
  last_scan: string | null;
  cache_age_seconds: number | null;
}

const Opportunities: React.FC = () => {
  const [opportunities, setOpportunities] = useState<StockOpportunity[]>([]);
  const [scanStatus, setScanStatus] = useState<ScanStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [filters, setFilters] = useState({
    signal: '',
    minScore: 60,
    sector: '',
    limit: 10
  });
  const [selectedStock, setSelectedStock] = useState<string>('');
  const [singleAnalysis, setSingleAnalysis] = useState<StockOpportunity | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch scan status on component mount
  useEffect(() => {
    console.log('Opportunities component mounted - starting data fetch');
    fetchScanStatus();
    fetchOpportunities();
  }, []);

  // Separate effect for polling that depends on scanStatus
  useEffect(() => {
    if (!scanStatus) return;

    console.log('Scan status:', scanStatus);
    
    const interval = setInterval(() => {
      fetchScanStatus();
      if (scanStatus.scan_in_progress) {
        fetchOpportunities();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [scanStatus]);

  const fetchScanStatus = async () => {
    try {
      console.log('Fetching scan status...');
      const response = await fetch('/opportunities/status');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      console.log('Scan status received:', data);
      setScanStatus(data);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch scan status:', error);
      setError('Failed to fetch scan status');
      // Set a default status so the component still renders
      setScanStatus({
        scan_in_progress: false,
        opportunities_cached: 0,
        last_scan: null,
        cache_age_seconds: null
      });
    }
  };

  const fetchOpportunities = async () => {
    try {
      console.log('Fetching opportunities...');
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.signal) params.append('signal', filters.signal);
      params.append('min_score', filters.minScore.toString());
      if (filters.sector) params.append('sector', filters.sector);
      params.append('limit', filters.limit.toString());

      const response = await fetch(`/opportunities/list?${params}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      console.log('Opportunities received:', data);
      setOpportunities(data.opportunities || []);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch opportunities:', error);
      setError('Failed to fetch opportunities');
      setOpportunities([]);
    } finally {
      setLoading(false);
    }
  };

  const startScan = async (maxStocks: number = 20) => {
    try {
      console.log(`Starting scan for ${maxStocks} stocks...`);
      setScanning(true);
      setError(null);
      const response = await fetch(`/opportunities/scan?max_stocks=${maxStocks}`, {
        method: 'GET'
      });
      const data = await response.json();
      console.log('Scan response:', data);
      
      if (data.status === 'scan_started') {
        // Poll for completion
        let pollCount = 0;
        const pollInterval = setInterval(async () => {
          await fetchScanStatus();
          await fetchOpportunities();
          pollCount++;
          
          // Check current status, not the stale closure value
          const statusResponse = await fetch('/opportunities/status');
          const currentStatus = await statusResponse.json();
          
          if (!currentStatus.scan_in_progress || pollCount > 20) {
            clearInterval(pollInterval);
            setScanning(false);
          }
        }, 3000);
      }
    } catch (error) {
      console.error('Failed to start scan:', error);
      setError('Failed to start scan');
      setScanning(false);
    }
  };

  const analyzeSingleStock = async () => {
    if (!selectedStock) return;
    
    try {
      console.log(`Analyzing stock: ${selectedStock}`);
      setLoading(true);
      setError(null);
      const response = await fetch(`/opportunities/analyze/${selectedStock.toUpperCase()}`);
      const data = await response.json();
      console.log('Analysis received:', data);
      setSingleAnalysis(data.analysis);
    } catch (error) {
      console.error('Failed to analyze stock:', error);
      setError('Failed to analyze stock');
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'STRONG_BUY': return 'bg-green-600 text-white';
      case 'BUY': return 'bg-green-500 text-white';
      case 'HOLD': return 'bg-yellow-500 text-black';
      case 'SELL': return 'bg-red-500 text-white';
      case 'STRONG_SELL': return 'bg-red-600 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const OpportunityCard: React.FC<{ opportunity: StockOpportunity }> = ({ opportunity }) => {
    try {
      return (
        <Card className="mb-4 bg-white dark:bg-gray-800">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-lg">{opportunity.ticker}</CardTitle>
                <CardDescription>{opportunity.company_name}</CardDescription>
              </div>
              <div className="text-right">
                <Badge className={getSignalColor(opportunity.ai_analysis.signal)}>
                  {opportunity.ai_analysis.signal}
                </Badge>
                <div className={`text-2xl font-bold ${getScoreColor(opportunity.ai_analysis.overall_score)}`}>
                  {opportunity.ai_analysis.overall_score.toFixed(1)}
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Price & Market Info */}
              <div>
                <h4 className="font-semibold mb-2">Market Data</h4>
                <div className="space-y-1 text-sm">
                  <div>Price: {formatCurrency(opportunity.current_price)}</div>
                  <div>Market Cap: ₹{(opportunity.market_cap).toFixed(0)}Cr</div>
                  <div>Sector: {opportunity.sector}</div>
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    Target: {formatCurrency(opportunity.ai_analysis.target_price)}
                  </div>
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4" />
                    Stop Loss: {formatCurrency(opportunity.ai_analysis.stop_loss)}
                  </div>
                </div>
              </div>

              {/* Technical Analysis */}
              <div>
                <h4 className="font-semibold mb-2">Technical Analysis</h4>
                <div className="space-y-1 text-sm">
                  <div>RSI: {opportunity.technical_indicators.rsi.toFixed(1)}</div>
                  <div>MACD: {opportunity.technical_indicators.macd_signal}</div>
                  <div>Trend: {opportunity.technical_indicators.moving_avg_trend}</div>
                  <div className="flex items-center gap-2">
                    {opportunity.technical_indicators.volume_surge ? (
                      <TrendingUp className="w-4 h-4 text-green-600" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-gray-400" />
                    )}
                    Volume Surge: {opportunity.technical_indicators.volume_surge ? 'Yes' : 'No'}
                  </div>
                  <div className={`font-medium ${getScoreColor(opportunity.ai_analysis.technical_score)}`}>
                    Technical Score: {opportunity.ai_analysis.technical_score.toFixed(1)}
                  </div>
                </div>
              </div>

              {/* Fundamental Analysis */}
              <div>
                <h4 className="font-semibold mb-2">Fundamentals</h4>
                <div className="space-y-1 text-sm">
                  <div>P/E Ratio: {opportunity.fundamental_metrics.pe_ratio.toFixed(1)}</div>
                  <div>ROE: {opportunity.fundamental_metrics.roe.toFixed(1)}%</div>
                  <div>Debt/Equity: {opportunity.fundamental_metrics.debt_to_equity.toFixed(2)}</div>
                  <div>Revenue Growth: {opportunity.fundamental_metrics.revenue_growth.toFixed(1)}%</div>
                  <div className={`font-medium ${getScoreColor(opportunity.ai_analysis.fundamental_score)}`}>
                    Fundamental Score: {opportunity.ai_analysis.fundamental_score.toFixed(1)}
                  </div>
                </div>
              </div>
            </div>

            {/* AI Reasoning */}
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold mb-2 text-green-600">Buy Reasons</h4>
                <ul className="text-sm space-y-1">
                  {opportunity.reasoning.buy_reasons.map((reason, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <TrendingUp className="w-3 h-3 mt-1 text-green-600 flex-shrink-0" />
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2 text-red-600">Risk Factors</h4>
                <ul className="text-sm space-y-1">
                  {opportunity.reasoning.risk_factors.map((risk, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <AlertTriangle className="w-3 h-3 mt-1 text-red-600 flex-shrink-0" />
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="mt-4 text-xs text-gray-500">
              Confidence: {(opportunity.ai_analysis.confidence * 100).toFixed(0)}%
            </div>
          </CardContent>
        </Card>
      );
    } catch (err) {
      console.error('Error rendering opportunity card:', err);
      return <div className="text-red-500">Error rendering opportunity</div>;
    }
  };

  // Main render with explicit styling
  return (
    <div className="w-full h-full overflow-auto" style={{ backgroundColor: 'white', color: 'black', minHeight: '100vh' }}>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2" style={{ color: 'black' }}>AI Stock Opportunities</h1>
          <p className="text-gray-600">
            AI-powered screening of NSE mid/small cap stocks for investment opportunities
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            Error: {error}
          </div>
        )}

        {/* Scan Status */}
        <Card className="mb-6 bg-white">
          <CardHeader>
            <CardTitle>Scan Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                {scanStatus ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      {scanStatus.scan_in_progress ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <div className="w-4 h-4 bg-green-500 rounded-full" />
                      )}
                      Status: {scanStatus.scan_in_progress ? 'Scanning...' : 'Ready'}
                    </div>
                    <div>Opportunities Cached: {scanStatus.opportunities_cached}</div>
                    {scanStatus.last_scan && (
                      <div>Last Scan: {new Date(scanStatus.last_scan).toLocaleString()}</div>
                    )}
                  </div>
                ) : (
                  <div>Loading status...</div>
                )}
              </div>
              <div className="space-x-2">
                <Button 
                  onClick={() => startScan(20)} 
                  disabled={scanning || (scanStatus?.scan_in_progress ?? false)}
                >
                  {scanning ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Scan 20 Stocks
                </Button>
                <Button 
                  onClick={() => startScan(50)} 
                  disabled={scanning || (scanStatus?.scan_in_progress ?? false)}
                  variant="outline"
                >
                  Scan 50 Stocks
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Tabs defaultValue="opportunities" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-gray-100">
            <TabsTrigger value="opportunities">Market Opportunities</TabsTrigger>
            <TabsTrigger value="analyze">Analyze Stock</TabsTrigger>
          </TabsList>

          <TabsContent value="opportunities" className="space-y-4">
            {/* Filters */}
            <Card className="bg-white">
              <CardHeader>
                <CardTitle>Filters</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <Label htmlFor="signal">Signal</Label>
                    <Select value={filters.signal} onValueChange={(value: string) => setFilters({...filters, signal: value})}>
                      <SelectTrigger>
                        <SelectValue placeholder="All signals" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">All Signals</SelectItem>
                        <SelectItem value="STRONG_BUY">Strong Buy</SelectItem>
                        <SelectItem value="BUY">Buy</SelectItem>
                        <SelectItem value="HOLD">Hold</SelectItem>
                        <SelectItem value="SELL">Sell</SelectItem>
                        <SelectItem value="STRONG_SELL">Strong Sell</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="minScore">Min Score</Label>
                    <Input
                      id="minScore"
                      type="number"
                      min="0"
                      max="100"
                      value={filters.minScore}
                      onChange={(e) => setFilters({...filters, minScore: parseInt(e.target.value) || 0})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="sector">Sector</Label>
                    <Input
                      id="sector"
                      placeholder="e.g., Technology"
                      value={filters.sector}
                      onChange={(e) => setFilters({...filters, sector: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="limit">Limit</Label>
                    <Input
                      id="limit"
                      type="number"
                      min="1"
                      max="50"
                      value={filters.limit}
                      onChange={(e) => setFilters({...filters, limit: parseInt(e.target.value) || 10})}
                    />
                  </div>
                </div>
                <Button onClick={fetchOpportunities} className="mt-4">
                  Apply Filters
                </Button>
              </CardContent>
            </Card>

            {/* Opportunities List */}
            {loading ? (
              <div className="flex justify-center items-center py-8">
                <Loader2 className="w-8 h-8 animate-spin" />
              </div>
            ) : opportunities.length > 0 ? (
              <div>
                {opportunities.map((opportunity, index) => (
                  <OpportunityCard key={`${opportunity.ticker}-${index}`} opportunity={opportunity} />
                ))}
              </div>
            ) : (
              <Card className="bg-white">
                <CardContent className="text-center py-8">
                  <p className="text-gray-500">No opportunities found. Try running a scan or adjusting filters.</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="analyze" className="space-y-4">
            <Card className="bg-white">
              <CardHeader>
                <CardTitle>Analyze Individual Stock</CardTitle>
                <CardDescription>
                  Get AI analysis for any NSE stock
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4">
                  <Input
                    placeholder="Enter stock ticker (e.g., RELIANCE)"
                    value={selectedStock}
                    onChange={(e) => setSelectedStock(e.target.value.toUpperCase())}
                    onKeyPress={(e) => e.key === 'Enter' && analyzeSingleStock()}
                  />
                  <Button onClick={analyzeSingleStock} disabled={!selectedStock || loading}>
                    {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    Analyze
                  </Button>
                </div>
              </CardContent>
            </Card>

            {singleAnalysis && (
              <OpportunityCard opportunity={singleAnalysis} />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export { Opportunities };
export default Opportunities; 