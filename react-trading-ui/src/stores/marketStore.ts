import { create } from 'zustand';
import type { Stock, StockQuote, ComprehensiveAnalysis } from '../types/api';
import { stocksAPI, analysisAPI } from '../services/api';

interface MarketStore {
  // State
  selectedStock: Stock | null;
  currentQuote: StockQuote | null;
  analysis: ComprehensiveAnalysis | null;
  searchResults: Stock[];
  watchlist: Stock[];
  topGainers: Stock[];
  topLosers: Stock[];
  mostActive: Stock[];
  
  // Loading states
  isLoadingQuote: boolean;
  isLoadingAnalysis: boolean;
  isLoadingSearch: boolean;
  isLoadingWatchlist: boolean;
  isLoadingMarketData: boolean;

  // Error states
  quoteError: string | null;
  analysisError: string | null;
  searchError: string | null;
  watchlistError: string | null;
  marketDataError: string | null;

  // WebSocket and polling
  webSocket: WebSocket | null;
  pollingInterval: NodeJS.Timeout | null;

  // Actions
  setSelectedStock: (stock: Stock | null) => void;
  searchStocks: (query: string) => Promise<void>;
  getStockQuote: (symbol: string) => Promise<void>;
  getAnalysis: (symbol: string) => Promise<void>;
  loadWatchlist: () => Promise<void>;
  addToWatchlist: (symbol: string) => Promise<void>;
  removeFromWatchlist: (symbol: string) => Promise<void>;
  loadMarketData: () => Promise<void>;
  startRealTimeUpdates: (symbol: string) => void;
  stopRealTimeUpdates: () => void;
  clearErrors: () => void;
  clearSearch: () => void;
}

export const useMarketStore = create<MarketStore>((set, get) => ({
  // Initial state
  selectedStock: null,
  currentQuote: null,
  analysis: null,
  searchResults: [],
  watchlist: [],
  topGainers: [],
  topLosers: [],
  mostActive: [],
  
  isLoadingQuote: false,
  isLoadingAnalysis: false,
  isLoadingSearch: false,
  isLoadingWatchlist: false,
  isLoadingMarketData: false,

  quoteError: null,
  analysisError: null,
  searchError: null,
  watchlistError: null,
  marketDataError: null,

  webSocket: null,
  pollingInterval: null,

  // Actions
  setSelectedStock: (stock: Stock | null) => {
    set({ 
      selectedStock: stock,
      currentQuote: null,
      analysis: null,
    });
    
    if (stock) {
      get().getStockQuote(stock.symbol);
      get().startRealTimeUpdates(stock.symbol);
    } else {
      get().stopRealTimeUpdates();
    }
  },

  searchStocks: async (query: string) => {
    if (!query.trim()) {
      set({ searchResults: [] });
      return;
    }

    set({ isLoadingSearch: true, searchError: null });

    try {
      const response = await stocksAPI.searchStocks(query);
      
      set({ 
        searchResults: response,
        isLoadingSearch: false 
      });
      
    } catch (error: any) {
      set({ 
        searchError: error.message || 'Search failed',
        isLoadingSearch: false 
      });
    }
  },

  getStockQuote: async (symbol: string) => {
    set({ isLoadingQuote: true, quoteError: null });

    try {
      const response = await stocksAPI.getQuote(symbol);
      
      set({ 
        currentQuote: response,
        isLoadingQuote: false 
      });
      
    } catch (error: any) {
      set({ 
        quoteError: error.message || 'Failed to load quote',
        isLoadingQuote: false 
      });
    }
  },

  getAnalysis: async (symbol: string) => {
    set({ isLoadingAnalysis: true, analysisError: null });

    try {
      const response = await analysisAPI.getComprehensiveAnalysis(symbol);
      
      set({ 
        analysis: response,
        isLoadingAnalysis: false 
      });
      
    } catch (error: any) {
      set({ 
        analysisError: error.message || 'Failed to load analysis',
        isLoadingAnalysis: false 
      });
    }
  },

  loadWatchlist: async () => {
    set({ isLoadingWatchlist: true, watchlistError: null });

    try {
      const response = await stocksAPI.getWatchlist();
      
      const watchlistStocks = response.map(symbol => ({ symbol, name: symbol }));
      set({ 
        watchlist: watchlistStocks,
        isLoadingWatchlist: false 
      });
      
    } catch (error: any) {
      set({ 
        watchlistError: error.message || 'Failed to load watchlist',
        isLoadingWatchlist: false 
      });
    }
  },

  addToWatchlist: async (symbol: string) => {
    try {
      await stocksAPI.addToWatchlist(symbol);
      
      // Reload watchlist to get updated data
      await get().loadWatchlist();
      
    } catch (error: any) {
      set({ watchlistError: error.message || 'Failed to add to watchlist' });
    }
  },

  removeFromWatchlist: async (symbol: string) => {
    try {
      await stocksAPI.removeFromWatchlist(symbol);
      
      // Remove from local state immediately
      set(state => ({
        watchlist: state.watchlist.filter(stock => stock.symbol !== symbol)
      }));
      
    } catch (error: any) {
      set({ watchlistError: error.message || 'Failed to remove from watchlist' });
    }
  },

  loadMarketData: async () => {
    set({ isLoadingMarketData: true, marketDataError: null });

    try {
      // For now, just set empty arrays - these endpoints need to be implemented
      set({
        topGainers: [],
        topLosers: [],
        mostActive: [],
        isLoadingMarketData: false
      });
    } catch (error: any) {
      set({ 
        marketDataError: error.message || 'Failed to load market data',
        isLoadingMarketData: false 
      });
    }
  },

  startRealTimeUpdates: (symbol: string) => {
    const state = get();
    
    // Stop existing updates
    state.stopRealTimeUpdates();

    // Simplified real-time updates with polling
    const interval = setInterval(async () => {
      try {
        const quote = await stocksAPI.getQuote(symbol);
        set({ currentQuote: quote });
      } catch (error) {
        console.error('Error updating quote:', error);
      }
    }, 5000);
    
    set({ pollingInterval: interval });
  },

  stopRealTimeUpdates: () => {
    const { webSocket, pollingInterval } = get();
    
    if (webSocket) {
      webSocket.close();
      set({ webSocket: null });
    }
    
    if (pollingInterval) {
      clearInterval(pollingInterval);
      set({ pollingInterval: null });
    }
  },

  clearErrors: () => {
    set({
      quoteError: null,
      analysisError: null,
      searchError: null,
      watchlistError: null,
      marketDataError: null,
    });
  },

  clearSearch: () => {
    set({ searchResults: [], searchError: null });
  },
}));