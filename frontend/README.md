# Trading Dashboard Frontend

A modern, real-time financial dashboard built with Next.js 15 and TypeScript.

## 🚀 Features

### **Real-Time Data Management**
- Custom `useRealTimeData` hook with intelligent polling
- Connection monitoring and retry logic
- Page visibility detection to pause updates when tab is inactive
- Configurable refresh intervals (optimized for development)

### **Interactive Components**
- **Market Overview**: Live indices, stocks, and crypto prices
- **Sentiment Analysis**: AI-powered social media sentiment from Reddit/StockTwits
- **Technical Analysis**: RSI, MACD, Moving Averages, Bollinger Bands
- **Earnings Calendar**: Upcoming earnings with pre/post market indicators
- **IPO Tracker**: New listings with pricing and company details
- **Watchlist Manager**: Personal portfolio tracking with Supabase sync

### **Advanced UI Features**
- **Smart Tooltips**: 5 specialized tooltip types with intelligent positioning
- **Responsive Design**: Mobile-optimized layouts
- **Loading States**: Skeleton screens and progress indicators
- **Error Boundaries**: Graceful error handling

## 🛠️ Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety and better developer experience
- **Tailwind CSS** - Utility-first styling framework
- **Supabase** - Authentication and real-time database
- **Custom Hooks** - Reusable logic for data fetching and state management

## 🏗️ Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── dashboard/         # Main dashboard page
│   ├── login/            # Authentication pages
│   └── register/         # User registration
├── components/            # Reusable React components
│   ├── common/           # Shared UI components
│   │   ├── SmartTooltip.tsx    # Advanced tooltip system
│   │   └── RealTimeStatus.tsx  # Connection status indicator
│   ├── dashboard/        # Dashboard-specific components
│   └── layout/          # Layout components
├── hooks/               # Custom React hooks
│   ├── useRealTimeData.ts     # Real-time data management
│   └── useMarketData.ts       # Market data specific hook
└── lib/                # Utilities and configurations
    └── supabase/       # Supabase client setup
```

## 🔧 Configuration

### Environment Variables

Create `.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Real-Time Data Intervals

Current refresh intervals (optimized for development):
- **Default**: 5 minutes
- **Market Data**: 2 minutes
- **Crypto Data**: 3 minutes
- **Sentiment Data**: 5 minutes
- **News**: 10 minutes

## 🚦 Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set up environment variables** (see above)

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Build for production**:
   ```bash
   npm run build
   npm start
   ```

## 🎯 Key Hooks & Utilities

### `useRealTimeData`
Comprehensive hook for managing real-time API data with features:
- Automatic reconnection on network issues
- Smart retry logic with exponential backoff
- Page visibility detection
- Connection status monitoring
- Configurable refresh intervals

### `SmartTooltip` Component
Advanced tooltip system with:
- **5 Specialized Types**: Financial, Sentiment, Technical, Earnings, News
- **Smart Positioning**: Automatically avoids screen edges
- **Rich Content**: Interactive data visualizations
- **Accessibility**: Keyboard navigation support

## 🔍 Performance Optimizations

- **React 18 Features**: Automatic batching, Suspense, Concurrent features
- **Next.js Optimizations**: Image optimization, automatic code splitting
- **Intelligent Caching**: SWR-style data fetching with stale-while-revalidate
- **Bundle Optimization**: Tree shaking, dynamic imports
- **Real-time Throttling**: Reduced API calls during development

## 🐛 Error Handling

- **Network Errors**: Automatic retry with user feedback
- **API Failures**: Graceful fallback to cached data
- **Component Errors**: Error boundaries prevent app crashes
- **Loading States**: Skeleton screens during data fetching

## 📱 Mobile Responsiveness

- **Tailwind Breakpoints**: Mobile-first responsive design
- **Touch Interactions**: Optimized for mobile devices
- **Adaptive Layouts**: Components adjust to screen size
- **Performance**: Optimized for mobile networks

---

Built with ❤️ using Next.js, TypeScript, and modern React patterns.