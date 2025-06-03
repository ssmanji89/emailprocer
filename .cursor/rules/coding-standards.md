---
description: Coding standards and conventions for EmailBot development
globs: ["dashboard/src/**/*.{ts,tsx}"]
alwaysApply: true
---

# Coding Standards - EmailBot

## TypeScript Standards

### Type Safety Requirements
- Use strict TypeScript mode
- No `any` types allowed - use proper interfaces
- Explicit return types for all functions
- Proper interface definitions for all props and data

```typescript
// ✅ Good
interface EscalationProps {
  escalation: Escalation
  onUpdate: (id: string, data: Partial<Escalation>) => void
}

export function EscalationCard({ escalation, onUpdate }: EscalationProps): JSX.Element {
  // Implementation
}

// ❌ Bad
export function EscalationCard({ escalation, onUpdate }: any) {
  // Implementation
}
```

### Import Organization
```typescript
// 1. React imports
import { useState, useEffect } from 'react'

// 2. Third-party imports
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, AlertCircle } from 'lucide-react'

// 3. Internal imports
import { apiClient } from '@/lib/api-client'
import { formatTimeAgo, getStatusColor } from '@/lib/utils'
import { Escalation } from '@/types/api'
```

## Component Structure Standards

### Standard Component Pattern
```typescript
'use client'

import { useState, useEffect } from 'react'
// ... other imports

interface ComponentProps {
  // Props definition
}

export function ComponentName({ prop }: ComponentProps) {
  // 1. State declarations
  const [data, setData] = useState<Type[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 2. Effect hooks
  useEffect(() => {
    loadData()
  }, [])

  // 3. Event handlers
  const handleAction = async () => {
    try {
      setIsLoading(true)
      setError(null)
      // Implementation
    } catch (error) {
      console.error('Action failed:', error)
      setError('Failed to perform action')
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
        <CardTitle>Component Title</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Component content */}
      </CardContent>
    </Card>
  )
}
```

## Error Handling Standards

### Async Operation Pattern
```typescript
const handleAsyncOperation = async () => {
  try {
    setIsLoading(true)
    setError(null)
    const result = await apiClient.operation()
    setData(result)
  } catch (error) {
    console.error('Operation failed:', error)
    setError('User-friendly error message')
  } finally {
    setIsLoading(false)
  }
}
```

### Error State Display
```typescript
// Always show user-friendly error messages
if (error) {
  return (
    <div className="flex items-center gap-2 p-4 text-red-600">
      <AlertCircle className="h-5 w-5" />
      {error}
    </div>
  )
}
```

## Naming Conventions

### Variables and Functions
- Use camelCase for variables and functions
- Use descriptive names that explain purpose
- Boolean variables should start with `is`, `has`, `can`, `should`

```typescript
// ✅ Good
const isLoading = true
const hasPermission = false
const canEdit = user.role === 'admin'
const escalationData = await apiClient.getEscalations()

// ❌ Bad
const loading = true
const perm = false
const edit = user.role === 'admin'
const data = await apiClient.getEscalations()
```

### Components and Types
- Use PascalCase for components and types
- Component names should be descriptive and specific
- Interface names should end with Props, Data, or Response

```typescript
// ✅ Good
interface EscalationCardProps {
  escalation: Escalation
}

export function EscalationCard({ escalation }: EscalationCardProps) {
  // Implementation
}

// ❌ Bad
interface Props {
  escalation: any
}

export function Card({ escalation }: Props) {
  // Implementation
}
```

## Performance Standards

### Loading States
- Always show loading indicators for async operations
- Use Loader2 with spin animation for consistency
- Disable interactive elements during loading

```typescript
<Button disabled={isLoading}>
  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
  {isLoading ? 'Processing...' : 'Submit'}
</Button>
```

### Debouncing for Search
```typescript
import { debounce } from '@/lib/utils'

const debouncedSearch = debounce((query: string) => {
  performSearch(query)
}, 300)
```

## Accessibility Standards

### ARIA Labels
```typescript
<Button
  aria-label="Delete escalation"
  aria-describedby="delete-description"
>
  <Trash2 className="h-4 w-4" />
</Button>
```

### Keyboard Navigation
- Ensure all interactive elements are keyboard accessible
- Use proper tab order
- Implement keyboard shortcuts where appropriate

## Code Quality Requirements

### Comments
- Use JSDoc for function documentation
- Comment complex business logic
- Avoid obvious comments

```typescript
/**
 * Calculates team workload score based on current assignments and capacity
 * @param teamId - The team identifier
 * @param assignments - Current active assignments
 * @returns Workload score between 0-100
 */
function calculateWorkloadScore(teamId: string, assignments: Assignment[]): number {
  // Complex calculation logic here
}
```

### File Organization
- One component per file
- File names should match component names
- Group related components in directories
- Keep files under 400 lines

### Testing Requirements
- Write unit tests for utility functions
- Test error handling scenarios
- Mock external dependencies
- Maintain test coverage above 80% 