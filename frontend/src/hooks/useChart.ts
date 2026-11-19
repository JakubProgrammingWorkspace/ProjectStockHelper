import { useEffect, useRef, useCallback } from 'react';
import { 
  createChart, 
  ColorType, 
  LineStyle, 
  SeriesMarker, 
  Time, 
  IChartApi, 
  ISeriesApi,
  CandlestickData,
  LineData,
  WhitespaceData
} from 'lightweight-charts';
import { StockPrice, FinancialMetric } from '../services/api';

interface ChartOptions {
  chartType: string;
  additionalData: string;
  logarithmicScale: boolean;
}

/**
 * Hook to manage lightweight-charts instance and rendering.
 */
const useChart = (
  container: HTMLDivElement | null,
  chartData: StockPrice[],
  volumeData: { time: string; volume: number }[],
  financialData: FinancialMetric[],
  options: ChartOptions
) => {
  const chartRef = useRef<IChartApi | null>(null);
  const mainSeriesRef = useRef<ISeriesApi<"Candlestick" | "Line" | "Bar"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const financialSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  const { chartType, additionalData, logarithmicScale } = options;

  const initChart = useCallback(() => {
    if (!container) return;

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: '#1e1e1e' },
        textColor: '#d1d4dc',
      },
      width: container.clientWidth,
      height: container.clientHeight,
      grid: {
        vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
        horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
      },
      rightPriceScale: {
        borderColor: 'rgba(197, 203, 206, 0.8)',
        mode: 1, // Always Logarithmic in v4
        autoScale: true,
        scaleMargins: {
          top: 0.05,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderColor: 'rgba(197, 203, 206, 0.8)',
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 0, // Normal
      },
    });

    chartRef.current = chart;

    // Volume series (bottom)
    volumeSeriesRef.current = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: { type: 'volume' },
      priceScaleId: '', // overlay
    });

    volumeSeriesRef.current.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0.05 },
    });

    // Add main series based on type
    if (chartType === 'candlestick') {
      mainSeriesRef.current = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      });
    } else if (chartType === 'bar') {
      mainSeriesRef.current = chart.addBarSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
      });
    } else {
      mainSeriesRef.current = chart.addLineSeries({
        color: '#2962FF',
        lineWidth: 2,
      });
    }

    // Add secondary scale for financials if needed
    if (additionalData !== 'none') {
      financialSeriesRef.current = chart.addLineSeries({
        color: '#f39c12',
        lineWidth: 2,
        priceScaleId: 'left',
      });

      chart.priceScale('left').applyOptions({
        autoScale: true,
        visible: true,
        borderColor: 'rgba(197, 203, 206, 0.8)',
        mode: logarithmicScale ? 1 : 0, // Set initial mode
        scaleMargins: {
          top: 0.05,
          bottom: 0.1,
        },
      });
    }

    const handleResize = () => {
      chart.applyOptions({
        width: container.clientWidth,
        height: container.clientHeight,
      });
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
    // Note: logarithmicScale removed from here to prevent full chart rebuilds
  }, [container, chartType, additionalData]);

  useEffect(() => {
    const cleanup = initChart();
    return () => {
      if (cleanup) cleanup();
    };
  }, [initChart]);

  // Handle scale mode changes independently
  useEffect(() => {
    if (!chartRef.current) return;
    
    // Only apply to left scale if it exists (Right scale is always log)
    if (additionalData !== 'none') {
      const mode = logarithmicScale ? 1 : 0;
      chartRef.current.priceScale('left').applyOptions({ mode });
    }
  }, [logarithmicScale, additionalData]);

  // Update Data
  useEffect(() => {
    if (!chartRef.current || !mainSeriesRef.current) return;

    // Main series data
    const formattedMainData = chartData.map(item => {
      if (chartType === 'candlestick' || chartType === 'bar') {
        return {
          time: item.date as Time,
          open: parseFloat(item.open_price),
          high: parseFloat(item.high_price),
          low: parseFloat(item.low_price),
          close: parseFloat(item.close_price),
        };
      } else {
        return {
          time: item.date as Time,
          value: parseFloat(item.close_price),
        };
      }
    });

    // Typescript needs help here because mainSeriesRef can be different types
    (mainSeriesRef.current as ISeriesApi<any>).setData(formattedMainData);

    // Volume data
    if (volumeSeriesRef.current) {
      const formattedVolume = chartData.map(item => {
        const isUp = parseFloat(item.close_price) >= parseFloat(item.open_price);
        return {
          time: item.date as Time,
          value: item.volume,
          color: isUp ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
        };
      });
      volumeSeriesRef.current.setData(formattedVolume);
    }

    // Financial data
    if (financialSeriesRef.current && financialData.length > 0) {
      const formattedFinancials = financialData.map(item => ({
        time: item.end_date as Time,
        value: item.value,
      }));
      financialSeriesRef.current.setData(formattedFinancials);
    }

    if (mainSeriesRef.current) {
      mainSeriesRef.current.setMarkers([]);
    }

    // Zoom to last 12 months on initial load or data change
    if (chartData.length > 0) {
      const lastPoint = chartData[chartData.length - 1];
      const lastDate = new Date(lastPoint.date);
      
      const oneYearAgo = new Date(lastDate);
      oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
      
      const oneYearAgoStr = oneYearAgo.toISOString().split('T')[0];
      
      // Find the first date in chartData that is >= oneYearAgo
      const fromIndex = chartData.findIndex(item => item.date >= oneYearAgoStr);

      if (fromIndex !== -1 && fromIndex < chartData.length - 5) {
        chartRef.current.timeScale().setVisibleRange({
          from: chartData[fromIndex].date as Time,
          to: lastPoint.date as Time,
        });
      } else {
        chartRef.current.timeScale().fitContent();
      }
    }
  }, [chartData, volumeData, financialData, chartType]);

  return chartRef.current;
};

export default useChart;
