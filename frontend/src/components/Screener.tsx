import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from "@/components/ui/button";

interface TickerResult {
  ticker: string;
  company_name: string;
  latest_close: number;
  chg_1d_pct?: number;
  chg_2d_pct?: number;
  chg_3d_pct?: number;
  chg_4d_pct?: number;
  chg_5d_pct?: number;
}

const Screener: React.FC = () => {
  const [fiftyTwoWeek, setFiftyTwoWeek] = useState('any');
  const [periodChange, setPeriodChange] = useState('any');
  
  const [results, setResults] = useState<TickerResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 50;

  const fetchResults = async (targetPage: number) => {
    // If all selectors are "any", don't fetch and show no results
    if (fiftyTwoWeek === 'any' && periodChange === 'any') {
      setResults([]);
      setTotalCount(0);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // Determine order direction based on filter type
      // For "down" filters, we want ascending (most negative first)
      const orderDir = periodChange.startsWith('down_') ? 'asc' : 'desc';

      const queryParams = new URLSearchParams({
        fiftyTwoWeek,
        periodChange,
        orderBy: 'priceChange',
        orderDir: orderDir,
        page: targetPage.toString(),
        pageSize: pageSize.toString(),
      });

      const response = await fetch(`/api/stock-data/screener/?${queryParams.toString()}`);
      if (!response.ok) {
        throw new Error('Failed to fetch screener results');
      }
      
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setResults(data.results || []);
      setTotalCount(data.total_count || 0);
    } catch (err: any) {
      setError(err.message || 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setPage(1);
    fetchResults(1);
  }, [fiftyTwoWeek, periodChange]);

  const handlePageChange = (newPage: number) => {
    if (newPage < 1 || newPage > Math.ceil(totalCount / pageSize)) return;
    setPage(newPage);
    fetchResults(newPage);
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="flex-1 flex flex-col p-6 bg-[#121212] overflow-hidden">
      <div className="bg-[#1e1e1e] p-6 rounded-lg border border-[#333] mb-6 shadow-md">
        <h2 className="text-2xl font-bold mb-4 text-white">Stock Screener</h2>

        <div className="flex flex-wrap gap-4 text-sm">
          {/* 52-Week High/Low */}
          <div className="flex items-center gap-2">
            <label className="text-gray-400 font-medium">52-Week High/Low</label>
            <select
              title="52-Week High/Low"
              value={fiftyTwoWeek}
              onChange={e => setFiftyTwoWeek(e.target.value)}
              className="bg-[#2a2a2a] text-white border border-[#444] rounded px-3 py-1.5 focus:outline-none focus:border-[#3498db]"
            >
              <option value="any">Any</option>
              <option value="new_high">New High</option>
              <option value="new_low">New Low</option>
              <option value="0-3_below">0-3% below High</option>
              <option value="0-5_below">0-5% below High</option>
              <option value="0-10_below">0-10% below High</option>
            </select>
          </div>

          {/* Max Price Change in Period */}
          <div className="flex items-center gap-2">
            <label className="text-gray-400 font-medium">Max Price Change in Period</label>
            <select
              title="Max Price Change in Period"
              value={periodChange}
              onChange={e => setPeriodChange(e.target.value)}
              className="bg-[#2a2a2a] text-white border border-[#444] rounded px-3 py-1.5 focus:outline-none focus:border-[#3498db]"
            >
              <option value="any">Any</option>
              <option value="up_1d" style={{ color: '#22c55e' }}>↑ 1d</option>
              <option value="up_2d" style={{ color: '#22c55e' }}>↑ 2d</option>
              <option value="up_3d" style={{ color: '#22c55e' }}>↑ 3d</option>
              <option value="up_4d" style={{ color: '#22c55e' }}>↑ 4d</option>
              <option value="up_5d" style={{ color: '#22c55e' }}>↑ 5d</option>
              <option value="down_1d" style={{ color: '#ef4444' }}>↓ 1d</option>
              <option value="down_2d" style={{ color: '#ef4444' }}>↓ 2d</option>
              <option value="down_3d" style={{ color: '#ef4444' }}>↓ 3d</option>
              <option value="down_4d" style={{ color: '#ef4444' }}>↓ 4d</option>
              <option value="down_5d" style={{ color: '#ef4444' }}>↓ 5d</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results Region */}
      <div className="flex-1 flex flex-col bg-[#1e1e1e] rounded-lg border border-[#333] overflow-hidden shadow-md">
        <div className="flex-1 overflow-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#252525] text-gray-300 text-sm uppercase tracking-wider sticky top-0 z-10 border-b border-[#333]">
                <th className="px-6 py-4 font-semibold">Ticker</th>
                <th className="px-6 py-4 font-semibold">Company Name</th>
                <th className="px-6 py-4 font-semibold text-right">Latest Close</th>
                <th className="px-6 py-4 font-semibold text-right">Selected Change*</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#333]">
              {fiftyTwoWeek === 'any' && periodChange === 'any' ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-400 italic">Select a filter to see results.</td>
                </tr>
              ) : loading ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-400">Loading...</td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-red-400">{error}</td>
                </tr>
              ) : results.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-400">No tickers match these criteria.</td>
                </tr>
              ) : (
                results.map((item) => {
                  // Determine which change to show based on filters
                  let changeStr = "-";
                  let actChange: number | undefined;

                  if (periodChange !== 'any') {
                    const period = periodChange.split('_')[1];
                    actChange = (item as any)[`chg_${period}_pct` || `chg_1d_pct` ];
                  } else {
                    actChange = item.chg_1d_pct;
                  }

                  if (actChange !== undefined && actChange !== null) {
                    changeStr = `${actChange > 0 ? '+' : ''}${actChange.toFixed(2)}%`;
                  }

                  return (
                    <tr key={item.ticker} className="hover:bg-[#2a2a2a] transition-colors group">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link 
                          to={`/${item.ticker}`}
                          className="text-[#3498db] font-bold group-hover:text-[#2980b9]"
                        >
                          {item.ticker}
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-300">
                        {item.company_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right font-mono">
                        ${item.latest_close.toFixed(2)}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-right font-mono ${actChange && actChange > 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {changeStr}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        {totalCount > pageSize && (
          <div className="px-6 py-4 flex items-center justify-between bg-[#252525] border-t border-[#333]">
            <div className="text-sm text-gray-400">
              Showing <span className="text-white font-medium">{(page - 1) * pageSize + 1}</span> to <span className="text-white font-medium">{Math.min(page * pageSize, totalCount)}</span> of <span className="text-white font-medium">{totalCount}</span> results
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(page - 1)}
                disabled={page === 1}
                className="bg-[#2a2a2a] border-[#444] text-white hover:bg-[#333] disabled:opacity-50"
              >
                Previous
              </Button>
              <div className="flex items-center px-4 text-sm text-gray-300">
                Page {page} of {totalPages}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(page + 1)}
                disabled={page === totalPages}
                className="bg-[#2a2a2a] border-[#444] text-white hover:bg-[#333] disabled:opacity-50"
              >
                Next
              </Button>
            </div>
          </div>
        )}

        <div className="p-4 bg-[#1a1a1a] text-xs text-gray-500 border-t border-[#333]">
          * Change is calculated between yesterday's close and the selected historical period.
        </div>
      </div>
    </div>
  );
};

export default Screener;
