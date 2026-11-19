import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import TickerSelector from '../TickerSelector';

describe('TickerSelector', () => {
  const mockTickers = [
    { ticker: 'AAPL', name: 'Apple Inc.' },
    { ticker: 'MSFT', name: 'Microsoft Corp' }
  ];

  it('renders loading state', () => {
    render(
      <TickerSelector 
        selectedTicker="" 
        onTickerChange={() => {}} 
        tickers={[]} 
        isLoading={true} 
        error={null} 
      />
    );
    expect(screen.getByText(/Loading tickers.../i)).toBeDefined();
  });

  it('renders error state', () => {
    render(
      <TickerSelector 
        selectedTicker="" 
        onTickerChange={() => {}} 
        tickers={[]} 
        isLoading={false} 
        error="Failed to fetch" 
      />
    );
    expect(screen.getByText(/Error: Failed to fetch/i)).toBeDefined();
  });

  it('renders tickers and handles change', () => {
    const onTickerChange = vi.fn();
    render(
      <TickerSelector 
        selectedTicker="AAPL" 
        onTickerChange={onTickerChange} 
        tickers={mockTickers} 
        isLoading={false} 
        error={null} 
      />
    );

    const select = screen.getByLabelText(/Ticker:/i);
    expect(select).toBeDefined();
    expect(screen.getByText(/AAPL - Apple Inc./i)).toBeDefined();
    expect(screen.getByText(/MSFT - Microsoft Corp/i)).toBeDefined();

    fireEvent.change(select, { target: { value: 'MSFT' } });
    expect(onTickerChange).toHaveBeenCalledWith('MSFT');
  });
});
