import React, { useState } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate, useParams } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import MainPanel from './components/MainPanel';
import { Button } from "@/components/ui/button";
import Screener from './components/Screener';

export const ROUTES = {
  CHART: '/',
  SCREENER: '/screener',
  DEFAULT_TICKER: '/NVDA'
};

interface ChartViewProps {
  timeInterval: string;
  setTimeInterval: (val: string) => void;
  chartType: string;
  setChartType: (val: string) => void;
  additionalData: string;
  setAdditionalData: (val: string) => void;
  logarithmicScale: boolean;
  setLogarithmicScale: (val: boolean) => void;
}

const ChartView: React.FC<ChartViewProps> = ({ 
  timeInterval, 
  setTimeInterval, 
  chartType, 
  setChartType, 
  additionalData, 
  setAdditionalData, 
  logarithmicScale, 
  setLogarithmicScale 
}) => {
  const { ticker } = useParams<{ ticker: string }>();
  const navigate = useNavigate();
  
  const activeTicker = ticker || 'NVDA';

  const handleTickerChange = (newTicker: string) => {
    navigate(`${ROUTES.CHART}${newTicker}`);
  };

  return (
    <div className="flex flex-1 overflow-hidden">
      <Sidebar
        selectedTicker={activeTicker}
        onTickerChange={handleTickerChange}
        timeInterval={timeInterval}
        onTimeIntervalChange={setTimeInterval}
        chartType={chartType}
        onChartTypeChange={setChartType}
        additionalData={additionalData}
        onAdditionalDataChange={setAdditionalData}
        logarithmicScale={logarithmicScale}
        onLogarithmicScaleChange={setLogarithmicScale}
      />
      <MainPanel
        selectedTicker={activeTicker}
        timeInterval={timeInterval}
        chartType={chartType}
        additionalData={additionalData}
        logarithmicScale={logarithmicScale}
      />
    </div>
  );
}

function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const [timeInterval, setTimeInterval] = useState('1D');
  const [chartType, setChartType] = useState('candlestick');
  const [additionalData, setAdditionalData] = useState('none');
  const [logarithmicScale, setLogarithmicScale] = useState(false);

  const isScreenerActive = location.pathname.startsWith(ROUTES.SCREENER);

  return (
    <div className="flex flex-col h-screen bg-[#121212] text-white dark">
      <nav className="bg-[#1e1e1e] px-5 py-[10px] border-b border-[#333] shadow-md z-10">
        <ul className="flex list-none m-0 p-0">
          <li className="mr-5">
            <Button
              variant={!isScreenerActive ? "default" : "ghost"}
              className={!isScreenerActive ? "bg-[#3498db] hover:bg-[#2980b9]" : "text-white hover:bg-[#333]"}
              onClick={() => navigate(ROUTES.CHART)}
            >
              Chart
            </Button>
          </li>
          <li className="mr-5">
            <Button
              variant={isScreenerActive ? "default" : "ghost"}
              className={isScreenerActive ? "bg-[#3498db] hover:bg-[#2980b9]" : "text-white hover:bg-[#333]"}
              onClick={() => navigate(ROUTES.SCREENER)}
            >
              Screener
            </Button>
          </li>
        </ul>
      </nav>

      <Routes>
        <Route path={ROUTES.SCREENER} element={<Screener />} />
        
        <Route path="/:ticker" element={
          <ChartView 
            timeInterval={timeInterval}
            setTimeInterval={setTimeInterval}
            chartType={chartType}
            setChartType={setChartType}
            additionalData={additionalData}
            setAdditionalData={setAdditionalData}
            logarithmicScale={logarithmicScale}
            setLogarithmicScale={setLogarithmicScale}
          />
        } />
        
        <Route path="/" element={<Navigate to={ROUTES.DEFAULT_TICKER} replace />} />
      </Routes>
    </div>
  );
}

export default App;
