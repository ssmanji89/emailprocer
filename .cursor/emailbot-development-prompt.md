# EmailBot Development Prompt for Cursor IDE

## System Overview
You are working on **EmailBot**, an enterprise-grade AI-powered email classification and escalation management system. This system provides real-time email processing, intelligent escalation management, team collaboration, and comprehensive analytics.

## Current System Status
- **4,747 lines** of production code implemented
- **13 major features** completed and operational
- **Next.js 14 + TypeScript + React 18** architecture
- **Real-time WebSocket** communication with auto-reconnection
- **Microsoft Teams integration** for team collaboration
- **shadcn/ui components** with Tailwind CSS styling

## Architecture & Tech Stack

### Frontend (dashboard/src/)
```
├── components/
│   ├── alerts/          # Real-time notifications (501 lines)
│   ├── charts/          # Analytics dashboards
│   ├── escalations/     # Escalation management UI (1,631 lines)
│   ├── forms/           # Form components
│   ├── modals/          # Dialog components (418 lines)
│   ├── navigation/      # Navigation components
│   ├── reports/         # Export & reporting (530 lines)
│   ├── tables/          # Data tables (460 lines)
│   └── ui/              # Base shadcn/ui components
├── lib/
│   ├── api-client.ts    # Centralized API client (333 lines)
│   ├── teams-service.ts # Microsoft Teams integration (319 lines)
│   ├── websocket.ts     # Real-time client (394 lines)
│   └── utils.ts         # Utility functions (350 lines)
└── types/
    └── api.ts           # TypeScript interfaces
```

### Technology Stack
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **UI Components**: shadcn/ui with Radix UI primitives
- **Icons**: Lucide React
- **State Management**: React hooks + localStorage + WebSocket
- **Real-time**: WebSocket with auto-reconnection
- **Backend**: Python (FastAPI/Flask, SQLAlchemy, Celery, Redis)
- **Integrations**: Microsoft Teams API, Export systems (PDF/CSV/XLSX)

## Implemented Features (All Complete ✅)

### Core Infrastructure (1,518 lines)
- **API Client Library** (333 lines) - Complete CRUD operations with error handling
- **Utilities Library** (350 lines) - Formatting, validation, localStorage helpers
- **Teams Integration Service** (319 lines) - Microsoft Teams management
- **WebSocket Client** (394 lines) - Real-time updates with React hooks
- **UI Dialog Component** (122 lines) - Accessible modal system

### Escalation Management (1,631 lines)
- **Team Assignment Modal** (418 lines) - AI-powered team recommendations
- **Escalation Timeline** (318 lines) - Visual activity tracking
- **Real-time Notifications** (501 lines) - SLA alerts, toast messages
- **Team Performance Dashboard** (394 lines) - Analytics with export

### Advanced Features (1,598 lines)
- **Advanced Search & Filtering** (440 lines) - Multi-dimensional search with saved queries
- **Bulk Operations Interface** (460 lines) - Multi-selection with progress tracking
- **SLA Management Dashboard** (580 lines) - Real-time SLA monitoring
- **Export & Reporting System** (530 lines) - Template-based reports

## Development Standards & Patterns

### Component Structure (ALWAYS FOLLOW)
```typescript
'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, AlertCircle } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { formatTimeAgo, getStatusColor } from '@/lib/utils'
import { ComponentProps } from '@/types/api'

export function ComponentName({ prop }: ComponentProps) {
  // 1. State declarations
  const [data, setData] = useState<Type[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 2. Effect hooks
  useEffect(() => {
    loadData()
  }, [])

  // 3. Event handlers with proper error handling
  const handleAction = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const result = await apiClient.operation()
      setData(result)
    } catch (error) {
      console.error('Action failed:', error)
      setError('User-friendly error message')
    } finally {
      setIsLoading(false)
    }
  }

  // 4. Early returns for loading/error states
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 text-red-600">
        <AlertCircle className="h-5 w-5" />
        {error}
      </div>
    )
  }

  // 5. Main render
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-5 w-5" />
          Component Title
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Component content */}
      </CardContent>
    </Card>
  )
}
```

### API Client Pattern (ALWAYS USE)
```typescript
// Add new methods to existing apiClient in lib/api-client.ts
export const apiClient = {
  async getEscalations(filters?: any): Promise<Escalation[]> {
    try {
      const response = await fetch('/api/escalations', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      if (!response.ok) throw new Error('API call failed')
      return response.json()
    } catch (error) {
      console.error('API Error:', error)
      throw error
    }
  }
}
```

### Utility Functions (USE EXISTING)
- `formatTimeAgo(date)` - Human-readable time (e.g., "2 hours ago")
- `formatDuration(seconds)` - Duration formatting (e.g., "2h 30m")
- `formatPercentage(value)` - Percentage with proper decimals
- `getStatusColor(status)` - Consistent status color mapping
- `downloadBlob(data, filename)` - File download helper
- `debounce(func, delay)` - Search input debouncing

### Real-time Pattern (FOR LIVE UPDATES)
```typescript
import { useWebSocket } from '@/lib/websocket'

const { isConnected, subscribe, unsubscribe } = useWebSocket()

useEffect(() => {
  const unsubscribeEscalation = subscribe('escalation.updated', handleUpdate)
  const unsubscribeSLA = subscribe('sla.breach', handleSLABreach)
  
  return () => {
    unsubscribeEscalation()
    unsubscribeSLA()
  }
}, [])
```

## Critical Development Rules

### 1. Type Safety (MANDATORY)
- **NO `any` types** - Use proper TypeScript interfaces
- **Explicit return types** for all functions
- **Interface definitions** for all props and data
- **Strict TypeScript mode** enabled

### 2. Error Handling (REQUIRED)
- **Try-catch blocks** around all async operations
- **User-friendly error messages** (not technical errors)
- **Loading states** for all async operations
- **Graceful degradation** when services fail

### 3. Component Standards (ENFORCE)
- **One component per file** with matching filename
- **PascalCase** for component names
- **camelCase** for variables and functions
- **Props interfaces** ending with "Props"
- **Files under 400 lines** maximum

### 4. UI/UX Standards (MAINTAIN)
- **shadcn/ui components** as base (Card, Button, Input, etc.)
- **Lucide React icons** for consistency
- **Loading states** with Loader2 spinning icon
- **WCAG compliant** with proper ARIA labels
- **Mobile-first responsive** design

### 5. Performance (OPTIMIZE)
- **Debounce search inputs** (300ms delay)
- **localStorage** for user preferences
- **Lazy loading** for large components
- **Proper dependency arrays** in useEffect

## Integration Points

### Microsoft Teams
- Use existing `teamsService` from `lib/teams-service.ts`
- Group creation and member management
- Real-time messaging integration
- Team performance tracking

### Real-time Features
- Use existing `useWebSocket` hook from `lib/websocket.ts`
- Auto-reconnection with exponential backoff
- Event types: escalation.updated, sla.breach, team.assigned
- Live UI updates without page refresh

### Export System
- Template-based report generation
- Multiple formats: PDF, CSV, XLSX
- Progress tracking with cancellation
- Streaming for large datasets

## Common Tasks & Patterns

### Adding New Component
1. Create in appropriate `components/` subdirectory
2. Follow standard component structure above
3. Use TypeScript interfaces for props
4. Implement proper error handling and loading states
5. Add to parent component imports

### Adding API Endpoint
1. Add method to `apiClient` in `lib/api-client.ts`
2. Define TypeScript interfaces in `types/api.ts`
3. Implement proper error handling
4. Update components to use new endpoint

### Adding Real-time Feature
1. Define event types in WebSocket client
2. Add event handlers in components using `useWebSocket`
3. Update subscription management
4. Test connection stability

### Form Implementation
```typescript
// Use existing form patterns with validation
const [formData, setFormData] = useState<FormData>({})
const [isSubmitting, setIsSubmitting] = useState(false)
const [error, setError] = useState<string | null>(null)

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  try {
    setIsSubmitting(true)
    setError(null)
    await apiClient.submitForm(formData)
    // Handle success
  } catch (error) {
    setError('Failed to submit form')
  } finally {
    setIsSubmitting(false)
  }
}
```

## Business Logic Context

### Email Escalation Workflow
1. Email received and classified by AI
2. Escalation triggered based on rules
3. Team assignment with AI recommendations
4. Real-time notifications to assigned team
5. Timeline tracking and status updates
6. Resolution and performance analytics

### Team Assignment Algorithm
- **Workload balancing** based on current capacity
- **Expertise matching** with email type
- **Availability checking** for team members
- **Historical performance** consideration
- **Geographic factors** (time zones)

### SLA Management
- **Breach prediction** with proactive alerts
- **Automatic escalation** when thresholds exceeded
- **Performance tracking** for compliance
- **Real-time monitoring** with dashboards

## Development Priorities

### Current Focus
1. **System Maintenance** (30%) - Keep existing features operational
2. **Feature Enhancement** (40%) - Improve and extend current features
3. **New Features** (20%) - Add new capabilities as requested
4. **Technical Debt** (10%) - Continuous improvement

### When Adding Features
- **Search existing code** first to avoid duplication
- **Follow established patterns** rather than creating new ones
- **Maintain consistency** with existing UI/UX
- **Test real-time functionality** thoroughly
- **Document complex business logic**

## Memory Bank System
The project uses a Memory Bank system in `.memory/` directory:
- `01-brief.md` - Project charter and goals
- `10-product.md` - Product definition and features
- `20-system.md` - System architecture
- `30-tech.md` - Technology landscape
- `40-active.md` - Current focus and state
- `50-progress.md` - Project trajectory
- `60-decisions.md` - Decision log
- `70-knowledge.md` - Domain knowledge

## Quick Reference Commands
```bash
# Development server
cd dashboard && npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Build
npm run build

# Tests
npm run test
```

## Success Metrics
- Email processing latency < 100ms
- Real-time updates < 50ms latency
- SLA compliance tracking and alerting
- Team workload optimization
- 99.9% system uptime
- WCAG 2.1 AA accessibility compliance

---

**Remember**: This is a mature, production-ready system with established patterns. Always follow existing conventions, maintain type safety, implement proper error handling, and ensure accessibility compliance. The system is designed for enterprise use with high reliability and performance standards. 