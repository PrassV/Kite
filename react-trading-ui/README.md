# Trading Analysis Platform - React Frontend

## Professional Trading Analysis with Real-time Technical Analysis

A modern React TypeScript frontend for the trading analysis platform that provides comprehensive technical analysis with Fibonacci retracements, volume patterns, and chart pattern detection.

### 🎯 Features

- **Modern React 18** with TypeScript for type safety
- **Responsive Design** with Tailwind CSS
- **Real-time Data** integration with FastAPI backend
- **Professional UI/UX** suitable for financial professionals
- **Comprehensive Analysis** display with tabbed interface
- **Authentication** via Kite Connect OAuth
- **State Management** with Zustand
- **API Integration** with React Query for caching and synchronization

### 🚀 Quick Start

#### Prerequisites
- Node.js 16+ 
- npm or yarn
- Backend API running (FastAPI on Railway)

#### Installation
```bash
# Clone and navigate to frontend directory
cd react-trading-ui

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Configure environment variables
# Edit .env with your backend API URL
REACT_APP_API_URL=https://your-railway-backend.railway.app
```

#### Development
```bash
# Start development server
npm run dev

# Open http://localhost:5173
```

### 🚀 Deployment

#### Vercel Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to Vercel
vercel

# Set environment variables in Vercel dashboard:
# REACT_APP_API_URL=https://your-railway-backend.railway.app
```

### 📊 Analysis Features

- **Landing Page**: Hero section with value proposition and feature highlights
- **Dashboard**: Stock search with autocomplete and popular stocks grid
- **Analysis Page**: Comprehensive analysis with Overview, Fibonacci, Patterns, Volume, and Recommendations tabs
- **Authentication**: Secure OAuth integration with Kite Connect
- **Real-time Data**: Live market data and analysis results

### 🔧 Technology Stack

- **React 18** with TypeScript
- **Vite** for fast development and builds
- **Tailwind CSS** for modern styling
- **Zustand** for state management
- **React Query** for server state
- **Framer Motion** for animations

**Built with ❤️ for professional traders**
