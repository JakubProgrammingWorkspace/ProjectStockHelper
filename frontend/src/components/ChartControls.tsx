import React from 'react';

interface ChartControlsProps {
  timeInterval: string;
  onTimeIntervalChange: (val: string) => void;
  chartType: string;
  onChartTypeChange: (val: string) => void;
  additionalData: string;
  onAdditionalDataChange: (val: string) => void;
  logarithmicScale: boolean;
  onLogarithmicScaleChange: (val: boolean) => void;
}

const ChartControls: React.FC<ChartControlsProps> = ({
  timeInterval,
  onTimeIntervalChange,
  chartType,
  onChartTypeChange,
  additionalData,
  onAdditionalDataChange,
  logarithmicScale,
  onLogarithmicScaleChange,
}) => {
  return (
    <>
      <div className="mb-[15px]">
        <label htmlFor="timeInterval" className="block mb-[5px] font-bold text-sm">Time interval:</label>
        <select
          id="timeInterval"
          value={timeInterval}
          onChange={(e) => onTimeIntervalChange(e.target.value)}
          className="w-full p-2 rounded border-none bg-[#2d2d2d] text-white focus:ring-1 focus:ring-[#3498db]"
        >
          <option value="1D">1 Day</option>
          <option value="2D">2 Days</option>
          <option value="3D">3 Days</option>
          <option value="4D">4 Days</option>
          <option value="Cu">Cumulative</option>
          <option value="1W">1 Week</option>
          <option value="1M">1 Month</option>
        </select>
      </div>

      <div className="mb-[15px]">
        <label htmlFor="chartType" className="block mb-[5px] font-bold text-sm">Chart Type:</label>
        <select
          id="chartType"
          value={chartType}
          onChange={(e) => onChartTypeChange(e.target.value)}
          className="w-full p-2 rounded border-none bg-[#2d2d2d] text-white focus:ring-1 focus:ring-[#3498db]"
        >
          <option value="candlestick">Candlestick</option>
          <option value="line">Line</option>
          <option value="bar">Bar</option>
        </select>
      </div>

      <div className="mb-[15px]">
        <label htmlFor="additionalData" className="block mb-[5px] font-bold text-sm">Additional Data:</label>
        <select
          id="additionalData"
          value={additionalData}
          onChange={(e) => onAdditionalDataChange(e.target.value)}
          className="w-full p-2 rounded border-none bg-[#2d2d2d] text-white focus:ring-1 focus:ring-[#3498db]"
        >
          <option value="none">None</option>
          <option value="revenue">Revenue</option>
          <option value="net_income">Net Income</option>
          <option value="revenue_ttm">Revenue TTM</option>
          <option value="net_income_ttm">Net Income TTM</option>
        </select>
      </div>

      <div className="mb-[15px] flex items-center space-x-2">
        <input
          type="checkbox"
          id="logarithmicScale"
          checked={logarithmicScale}
          onChange={(e) => onLogarithmicScaleChange(e.target.checked)}
          className="rounded bg-[#2d2d2d] border-none text-[#3498db] focus:ring-offset-[#1e1e1e]"
        />
        <label htmlFor="logarithmicScale" className="font-bold text-sm cursor-pointer">Logarithmic</label>
      </div>
    </>
  );
};

export default ChartControls;
