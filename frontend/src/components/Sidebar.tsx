import React, { useState } from 'react';
import { api } from '../services/api';
import { useAvailableTickers } from '../hooks/useAvailableTickers';
import TickerSelector from './TickerSelector';
import ChartControls from './ChartControls';
import ExternalLinks from './ExternalLinks';

interface SidebarProps {
  selectedTicker: string;
  onTickerChange: (ticker: string) => void;
  timeInterval: string;
  onTimeIntervalChange: (val: string) => void;
  chartType: string;
  onChartTypeChange: (val: string) => void;
  additionalData: string;
  onAdditionalDataChange: (val: string) => void;
  logarithmicScale: boolean;
  onLogarithmicScaleChange: (val: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  selectedTicker,
  onTickerChange,
  timeInterval,
  onTimeIntervalChange,
  chartType,
  onChartTypeChange,
  additionalData,
  onAdditionalDataChange,
  logarithmicScale,
  onLogarithmicScaleChange
}) => {
  const { tickers, isLoading, error } = useAvailableTickers();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    if (!selectedTicker) return;

    setIsRefreshing(true);
    try {
      const response = await api.refreshTickerData(selectedTicker);
      // Backend returns { message: string, records_updated: number }
      if (response && (response as any).message) {
        window.dispatchEvent(new CustomEvent('tickerDataRefreshed', { detail: selectedTicker }));
      } else {
        console.error('Error refreshing data: Unexpected response format', response);
      }
    } catch (err: any) {
      console.error('Error refreshing ticker data:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="w-1/5 bg-[#1e1e1e] p-5 overflow-y-auto border-r border-[#333]">
      <TickerSelector 
        selectedTicker={selectedTicker}
        onTickerChange={onTickerChange}
        tickers={tickers}
        isLoading={isLoading}
        error={error}
      />

      <ChartControls 
        timeInterval={timeInterval}
        onTimeIntervalChange={onTimeIntervalChange}
        chartType={chartType}
        onChartTypeChange={onChartTypeChange}
        additionalData={additionalData}
        onAdditionalDataChange={onAdditionalDataChange}
        logarithmicScale={logarithmicScale}
        onLogarithmicScaleChange={onLogarithmicScaleChange}
      />

      <button
        className="w-full py-[10px] bg-[#4CAF50] text-white border-none rounded cursor-pointer font-bold mt-[10px] hover:bg-[#45a049] disabled:bg-[#666] disabled:cursor-not-allowed transition-all shadow-lg active:scale-95"
        onClick={handleRefresh}
        disabled={isRefreshing || !selectedTicker}
      >
        {isRefreshing ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Refreshing...
          </span>
        ) : 'Refresh'}
      </button>

      <ExternalLinks selectedTicker={selectedTicker} />
    </div>
  );
};

export default Sidebar;
