import { useState, useEffect, useCallback } from 'react';
import { api, FinancialMetric } from '../services/api';

/**
 * Fetches additional financial data for a given ticker and data type.
 */
const useFinancialData = (ticker: string | undefined, dataType: string) => {
  const [financialData, setFinancialData] = useState<FinancialMetric[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFinancialData = useCallback(async (isMounted: boolean) => {
    if (!ticker || dataType === 'none') {
      setFinancialData([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await api.getFinancialData(ticker, dataType);
      
      if (isMounted) {
        setFinancialData(data.financials || []);
      }
    } catch (err: any) {
      console.error('Error fetching financial data:', err);
      if (isMounted) {
        setError(err.message);
      }
    } finally {
      if (isMounted) {
        setIsLoading(false);
      }
    }
  }, [ticker, dataType]);

  useEffect(() => {
    let isMounted = true;
    fetchFinancialData(isMounted);
    return () => {
      isMounted = false;
    };
  }, [fetchFinancialData]);

  useEffect(() => {
    const handleRefresh = (event: any) => {
      if (event.detail === ticker) {
        fetchFinancialData(true);
      }
    };

    window.addEventListener('tickerDataRefreshed', handleRefresh);
    return () => {
      window.removeEventListener('tickerDataRefreshed', handleRefresh);
    };
  }, [ticker, fetchFinancialData]);

  return { financialData, isLoading, error };
};

export default useFinancialData;
