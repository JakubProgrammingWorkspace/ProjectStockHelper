/**
 * API service for interacting with the StockHelper backend.
 * Uses relative paths to work seamlessly in both dev (proxy) and production.
 */

export interface TickerInfo {
  ticker: string;
  name: string;
}

export interface StockPrice {
  date: string;
  open_price: string;
  high_price: string;
  low_price: string;
  close_price: string;
  volume: number;
}

export interface FinancialMetric {
  end_date: string;
  value: number;
}


const fetchJson = async <T>(url: string | URL): Promise<T> => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  return response.json();
};

export const api = {
  /**
   * Fetches the list of available stock tickers.
   */
  getTickers: (): Promise<{ tickers: TickerInfo[] }> => 
    fetchJson('/api/tickers/'),

  /**
   * Fetches historical price data for a specific ticker.
   */
  getStockPrices: (ticker: string, interval: string): Promise<{ prices: StockPrice[] }> => 
    fetchJson(`/api/stock-data/${ticker}/?time_interval=${interval}`),

  /**
   * Fetches additional financial data (e.g. revenue, net income).
   */
  getFinancialData: (ticker: string, dataType: string): Promise<{ financials: FinancialMetric[] }> =>
    fetchJson(`/api/additional-financial-data/${ticker}/?data_type=${dataType}`),


  /**
   * Triggers a manual refresh of ticker data from external sources.
   */
  refreshTickerData: (ticker: string): Promise<{ status: string; error?: string }> =>
    fetchJson(`/api/refresh-ticker-data/${ticker}/`),
};
