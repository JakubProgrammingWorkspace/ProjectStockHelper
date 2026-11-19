import { useState, useEffect } from 'react';
import { api, TickerInfo } from '../services/api';

/**
 * Custom hook for fetching and managing available stock tickers.
 */
export const useAvailableTickers = () => {
  const [tickers, setTickers] = useState<TickerInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchTickers = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await api.getTickers();
        if (isMounted) {
          setTickers(data.tickers || []);
        }
      } catch (err: any) {
        console.error('Error fetching tickers:', err);
        if (isMounted) {
          setError(err.message);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchTickers();
    return () => {
      isMounted = false;
    };
  }, []);

  return { tickers, isLoading, error };
};
