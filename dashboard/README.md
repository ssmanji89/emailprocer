# EmailBot Dashboard

A modern, responsive web dashboard for the EmailBot AI email processing system. Built with Next.js, TypeScript, and Tailwind CSS.

## 🎯 Overview

The EmailBot Dashboard provides comprehensive analytics and management capabilities for the AI-powered email classification and response system. It offers real-time monitoring, detailed analytics, and administrative controls for the email processing pipeline.

## 🚀 Features

### ✅ **Currently Implemented**

#### Core Dashboard
- **Real-time Overview**: Live system status and key metrics
- **Health Monitoring**: System component health checks
- **Processing Statistics**: Email processing volume, success rates, and timing
- **Classification Metrics**: AI classification accuracy and confidence scores

#### Processing Analytics
- **Performance Trends**: Daily processing volume charts
- **Time-based Analysis**: Processing time trends and patterns  
- **Success/Failure Tracking**: Detailed breakdown of processing outcomes
- **Manual Triggers**: On-demand processing initiation

#### Classification Analytics
- **Category Distribution**: Interactive pie and bar charts showing email classification breakdown
- **Confidence Analysis**: Histogram and scatter plots of confidence scores
- **Human Feedback Interface**: Modal form for submitting classification feedback
- **Model Performance**: Insights dashboard with confidence threshold analysis
- **Real-time Metrics**: Live classification accuracy and feedback statistics

#### Navigation & UI
- **Responsive Design**: Mobile-first approach with desktop optimization
- **Modern Interface**: Clean, intuitive design with consistent theming
- **Real-time Updates**: Live data refresh every 5-30 seconds
- **Loading States**: Proper feedback for async operations

### 🚧 **Planned Features**

#### Pattern Management
- Automation opportunity visualization
- Pattern frequency and impact analysis
- Pattern approval/rejection workflow
- ROI calculator for automation potential

#### Email History & Search
- Searchable email processing history
- Advanced filtering capabilities
- Email detail view with classification reasoning
- Processing workflow timeline

#### Escalation Management
- Active escalation teams dashboard
- Team performance metrics
- Escalation resolution interface
- Historical analysis and trends

## 🛠️ Tech Stack

- **Framework**: Next.js 15.3.3 with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS with CSS variables for theming
- **UI Components**: Custom components built with Radix UI primitives
- **Charts**: Recharts for data visualization
- **State Management**: TanStack React Query for server state
- **Icons**: Lucide React icon library
- **Date Handling**: date-fns for date formatting and manipulation

## 📦 Installation

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Running EmailBot FastAPI backend on `localhost:8000`

### Setup Steps

1. **Install Dependencies**
   ```bash
   cd dashboard
   npm install
   ```

2. **Environment Configuration**
   Create a `.env.local` file:
   ```bash
   # API Configuration
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   
   # Dashboard Features
   NEXT_PUBLIC_ENABLE_REAL_TIME=true
   NEXT_PUBLIC_REFRESH_INTERVAL=5000
   
   # Development
   NODE_ENV=development
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

4. **Access Dashboard**
   Open [http://localhost:3000](http://localhost:3000) in your browser

## 🏗️ Project Structure

```
dashboard/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── dashboard/          # Main dashboard page
│   │   ├── analytics/          # Analytics pages
│   │   │   ├── processing/     # Processing analytics
│   │   │   └── classification/ # Classification analytics
│   │   ├── patterns/           # Pattern management (planned)
│   │   └── escalations/        # Escalation management (planned)
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Base UI components (Button, Card, etc.)
│   │   ├── charts/             # Chart components (Processing, Category, Confidence)
│   │   ├── forms/              # Form components (Feedback form)
│   │   └── navigation/         # Navigation components
│   ├── lib/                    # Utility libraries
│   │   ├── api-client.ts       # API communication layer
│   │   ├── utils.ts            # Utility functions
│   │   └── providers.tsx       # React providers (Query Client)
│   ├── hooks/                  # Custom React hooks (planned)
│   └── types/                  # TypeScript type definitions
│       └── api.ts              # API response types
├── public/                     # Static assets
├── package.json                # Dependencies and scripts
├── tailwind.config.ts          # Tailwind CSS configuration
├── tsconfig.json               # TypeScript configuration
└── next.config.ts              # Next.js configuration
```

## 🔗 API Integration

The dashboard integrates with the following EmailBot FastAPI endpoints:

### Health & Status
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed component health
- `GET /process/status` - Processing pipeline status

### Dashboard Analytics
- `GET /analytics/dashboard` - Main dashboard metrics
- `GET /analytics/processing?days=7` - Processing analytics
- `GET /analytics/classification` - Classification metrics with category distribution
- `GET /analytics/patterns` - Pattern analysis (planned)

### Control Operations
- `POST /process/trigger` - Manually trigger email processing
- `POST /analytics/feedback` - Submit human feedback for classification accuracy
- `GET /emails/history` - Email processing history (planned)

## 🎨 Design System

### Color Scheme
- **Primary**: Blue (#3b82f6) for actions and highlights
- **Success**: Green (#22c55e) for positive metrics
- **Warning**: Yellow (#f59e0b) for attention items
- **Error**: Red (#ef4444) for failures and alerts
- **Neutral**: Gray scale for text and backgrounds

### Component Library
- **Cards**: Consistent containers for related information
- **Buttons**: Multiple variants (default, outline, ghost, destructive)
- **Charts**: Responsive data visualizations with tooltips
- **Navigation**: Sidebar with active state indicators

### Responsive Breakpoints
- **Mobile**: 640px and below
- **Tablet**: 641px - 1024px  
- **Desktop**: 1025px and above

## 📊 Data Flow

1. **Real-time Updates**: Components use React Query with automatic refresh intervals
2. **Error Handling**: Graceful degradation with user-friendly error messages
3. **Loading States**: Skeleton loading and spinner indicators
4. **Caching**: Intelligent caching with stale-while-revalidate strategy

## 🚀 Deployment

### Development
```bash
npm run dev     # Start development server
npm run build   # Build for production
npm run start   # Start production server
npm run lint    # Run ESLint
```

### Production Considerations
- Configure `NEXT_PUBLIC_API_BASE_URL` for production API
- Set up proper error monitoring (Sentry, etc.)
- Configure analytics (Google Analytics, etc.)
- Set up CI/CD pipeline for automated deployments

## 🔮 Future Enhancements

### Phase 5.3: Pattern Management (Next Priority)
- **Category Distribution Charts**: Pie/bar charts showing email categories
- **Confidence Analysis**: Distribution of classification confidence scores
- **Feedback Interface**: Human feedback collection for AI improvement
- **Trend Analysis**: Classification accuracy trends over time

### Phase 5.3: Pattern Management
- **Automation Candidates**: Table of identified automation opportunities
- **Pattern Approval Workflow**: Review and approve automation patterns
- **ROI Calculator**: Potential time savings from automation
- **Pattern Performance Tracking**: Monitor automation success rates

### Phase 5.4: Advanced Features
- **Email Search & History**: Comprehensive email processing history
- **Escalation Management**: Teams dashboard and resolution workflow
- **User Authentication**: NextAuth.js with M365 integration
- **Export Capabilities**: PDF/CSV report generation
- **Dark Mode**: Theme toggle with system preference detection

## 🤝 Contributing

1. Follow the established TypeScript and React patterns
2. Use the existing component library for consistency
3. Add proper error handling and loading states
4. Include responsive design considerations
5. Update type definitions for new API endpoints

## 📝 Notes

- **Backend Dependency**: Requires EmailBot FastAPI backend running on port 8000
- **Real-time Data**: Dashboard automatically refreshes data every 5-30 seconds
- **Type Safety**: Full TypeScript coverage for API responses and components
- **Performance**: Optimized with React Query caching and lazy loading

## 🎯 Current Status

**Phase 5.1 Complete**: Foundation, authentication setup, core dashboard, and processing analytics are fully implemented and functional. The dashboard successfully connects to the EmailBot backend and displays real-time processing metrics with interactive charts.

Ready for Phase 5.2 development focusing on classification analytics and pattern management features.
