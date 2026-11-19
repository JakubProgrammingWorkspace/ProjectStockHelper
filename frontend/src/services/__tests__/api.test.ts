import { describe, it, expect } from 'vitest';
import { api } from '../api';

describe('api service', () => {
  it('getTickers returns tickers from MSW', async () => {
    const data = await api.getTickers();
    expect(data.tickers).toHaveLength(2);
    expect(data.tickers[0].ticker).toBe('AAPL');
  });
});
