# System Architecture - EmailBot

## Overall Architecture
EmailBot follows a modern full-stack architecture with clear separation of concerns:

```
Frontend (Next.js 14) ↔ API Layer ↔ Backend Services ↔ External Integrations
     ↓                      ↓              ↓                    ↓
  React Components    RESTful APIs    Email Processing    Microsoft Teams
  Real-time UI        WebSocket       AI Classification   Notification Systems
  State Management    Error Handling  Database Layer      Export Services
```

## Project Structure

### Frontend Architecture (`dashboard/src/`)
```
dashboard/src/
├── components/
│   ├── alerts/          # Real-time notifications
│   ├── charts/          # Analytics dashboards  
│   ├── escalations/     # Escalation management UI
│   ├── forms/           # Form components
│   ├── modals/          # Dialog components
│   ├── navigation/      # Navigation components
│   ├── reports/         # Export & reporting
│   ├── tables/          # Data tables
│   └── ui/              # Base UI components (shadcn/ui)
├── lib/
│   ├── api-client.ts    # Centralized API client
│   ├── teams-service.ts # Microsoft Teams integration
│   ├── websocket.ts     # Real-time client
│   └── utils.ts         # Utility functions
└── types/
    └── api.ts           # TypeScript interfaces
```

### Backend Architecture (`app/`)
```
app/
├── config/              # Configuration management
├── core/                # Core business logic
├── integrations/        # External service integrations
├── middleware/          # Request/response middleware
├── models/              # Data models and schemas
├── services/            # Business services
└── utils/               # Utility functions
```

## Data Flow Patterns

### Email Processing Flow
1. **Ingestion**: Email received via API/webhook
2. **Classification**: AI-powered categorization
3. **Routing**: Rule-based escalation logic
4. **Assignment**: Team recommendation algorithm
5. **Notification**: Real-time updates via WebSocket
6. **Tracking**: Timeline and status management

### Real-time Communication
- **WebSocket Client**: Auto-reconnection with React hooks
- **Event Types**: Escalation updates, SLA alerts, team assignments
- **State Synchronization**: Live UI updates without page refresh
- **Error Handling**: Graceful degradation and retry logic

### API Design Patterns
- **RESTful Endpoints**: Standard CRUD operations
- **Centralized Client**: Single API client with error handling
- **Type Safety**: TypeScript interfaces for all data
- **Error Boundaries**: Consistent error handling across components

## Component Architecture Patterns

### Standard Component Structure
```typescript
'use client'
// Imports: React hooks, UI components, utilities, types
// Interface: Props definition with TypeScript
// State: Local state management with useState
// Effects: Data loading with useEffect
// Handlers: Event handling functions
// Render: JSX with proper error/loading states
```

### State Management Strategy
- **Local State**: Component-level with React hooks
- **Persistent State**: localStorage for user preferences
- **Real-time State**: WebSocket subscriptions
- **API State**: Centralized through api-client

### Integration Patterns
- **Microsoft Teams**: Service layer with group management
- **Export System**: Template-based report generation
- **Real-time Updates**: WebSocket with event-driven architecture
- **Error Handling**: Consistent patterns across all integrations

## Security Architecture
- **Type Safety**: Full TypeScript implementation
- **Input Validation**: Client and server-side validation
- **Error Handling**: Secure error messages and logging
- **Access Control**: Role-based permissions (planned)
- **Data Protection**: Secure API communication

## Performance Patterns
- **Lazy Loading**: Component-level code splitting
- **Debouncing**: Search input optimization
- **Caching**: localStorage for user preferences
- **Real-time Optimization**: Efficient WebSocket event handling
- **Bundle Optimization**: Tree shaking and code splitting 