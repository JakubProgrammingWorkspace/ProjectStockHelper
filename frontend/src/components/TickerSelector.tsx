import React from 'react';
import { TickerInfo } from '../services/api';

interface TickerSelectorProps {
  selectedTicker: string;
  onTickerChange: (ticker: string) => void;
  tickers: TickerInfo[];
  isLoading: boolean;
  error: string | null;
}

const TickerSelector: React.FC<TickerSelectorProps> = ({ 
  selectedTicker, 
  onTickerChange, 
  tickers, 
  isLoading, 
  error 
}) => {
  if (isLoading) return <div className="mb-4 text-gray-400">Loading tickers...</div>;
  if (error) return <div className="mb-4 text-red-500 text-sm">Error: {error}</div>;

  return (
    <div className="mb-[15px]">
      <label htmlFor="ticker" className="block mb-[5px] font-bold">Ticker:</label>
      <select
        id="ticker"
        value={selectedTicker}
        onChange={(e) => onTickerChange(e.target.value)}
        className="w-full p-2 rounded border-none bg-[#2d2d2d] text-white focus:ring-2 focus:ring-[#3498db] transition-all"
      >
        {tickers.map(ticker => (
          <option key={ticker.ticker} value={ticker.ticker}>
            {ticker.ticker} - {ticker.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default TickerSelector;
