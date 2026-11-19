import React, { useRef } from 'react';
import useStockData from '../hooks/useStockData';
import useFinancialData from '../hooks/useFinancialData';
import useChart from '../hooks/useChart';

interface MainPanelProps {
  selectedTicker: string;
  timeInterval: string;
  chartType: string;
  additionalData: string;
  logarithmicScale: boolean;
}

const MainPanel: React.FC<MainPanelProps> = ({
  selectedTicker,
  timeInterval,
  chartType,
  additionalData,
  logarithmicScale,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);

  const { 
    chartData, 
    volumeData, 
    isLoading: isStockLoading, 
    error: stockError 
  } = useStockData(selectedTicker, timeInterval);
  
  const { 
    financialData, 
    isLoading: isFinancialLoading 
  } = useFinancialData(selectedTicker, additionalData);
  

  useChart(
    chartContainerRef.current,
    chartData,
    volumeData,
    financialData,
    { chartType, additionalData, logarithmicScale }
  );

  const isLoading = isStockLoading || isFinancialLoading;

  return (
    <div className="flex-1 flex flex-col p-5 bg-[#121212]">
      <div className="mb-1 flex justify-end items-center">
        {isLoading && (
          <div className="flex items-center text-sm text-[#3498db]">
            <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Updating...
          </div>
        )}
      </div>

      <div className="flex-1 bg-[#1e1e1e] rounded-lg p-[10px] relative min-h-[400px]">
        {stockError ? (
          <div className="flex flex-col items-center justify-center h-full text-red-500">
             <span className="text-4xl mb-2">⚠️</span>
             <p>Error loading chart: {stockError}</p>
          </div>
        ) : (
          <div ref={chartContainerRef} className="w-full h-full" />
        )}
      </div>

      <div className="mt-4 text-[10px] text-gray-500 flex justify-center items-center space-x-1">
        <span>TradingView Lightweight Charts™</span>
        <span>Copyright (с) 2025 TradingView, Inc.</span>
        <a href="https://www.tradingview.com/" target="_blank" rel="noopener noreferrer" className="hover:underline text-gray-400">www.tradingview.com</a>
      </div>
    </div>
  );
};

export default MainPanel;
