import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/tickers/', () => {
    return HttpResponse.json({
      tickers: [
        { ticker: 'AAPL', name: 'Apple Inc.' },
        { ticker: 'MSFT', name: 'Microsoft Corp' },
      ],
    });
  }),
];
