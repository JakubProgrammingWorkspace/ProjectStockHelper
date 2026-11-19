import { useState, useEffect, useCallback } from 'react';
import { api, StockPrice } from '../services/api';

export interface VolumeData {
  time: string;
  volume: number;
}

/**
 * Fetches OHLCV stock data for a given ticker and time interval.
 * Returns chartData, volumeData, loading/error states, and a refetch function.
 */
const useStockData = (ticker: string | undefined, interval: string) => {
  const [chartData, setChartData] = useState<StockPrice[]>([]);
  const [volumeData, setVolumeData] = useState<VolumeData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!ticker) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await api.getStockPrices(ticker, interval);
      const prices = data.prices ?? [];
      setChartData(prices);

      const vol = prices
        .map(item => ({ time: item.date, volume: item.volume }))
        .filter(item => item.volume !== null && item.volume !== undefined);
      setVolumeData(vol);
    } catch (err: any) {
      console.error('Error fetching stock data:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [ticker, interval]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    const handleRefresh = (event: any) => {
      if (event.detail === ticker) {
        fetchData();
      }
    };

    window.addEventListener('tickerDataRefreshed', handleRefresh);
    return () => {
      window.removeEventListener('tickerDataRefreshed', handleRefresh);
    };
  }, [ticker, fetchData]);

  return { chartData, volumeData, isLoading, error, refetch: fetchData };
};

export default useStockData;
