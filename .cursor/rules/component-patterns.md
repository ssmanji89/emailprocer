---
description: Component patterns and reusable templates for EmailBot
globs: ["dashboard/src/components/**/*.{ts,tsx}"]
alwaysApply: true
---

# Component Patterns - EmailBot

## Standard Component Templates

### Basic Data Display Component
```typescript
'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { formatTimeAgo } from '@/lib/utils'

interface DataDisplayProps {
  title: string
  endpoint: string
  refreshInterval?: number
}

export function DataDisplay({ title, endpoint, refreshInterval }: DataDisplayProps) {
  const [data, setData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const result = await apiClient.get(endpoint)
      setData(result)
      setLastUpdated(new Date())
    } catch (error) {
      console.error(`Failed to load ${title}:`, error)
      setError(`Failed to load ${title}`)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    
    if (refreshInterval) {
      const interval = setInterval(loadData, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [endpoint, refreshInterval])

  if (isLoading && data.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{title}</CardTitle>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            Updated {formatTimeAgo(lastUpdated)}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="flex items-center gap-2 p-4 text-red-600">
            <AlertCircle className="h-5 w-5" />
            {error}
          </div>
        ) : (
          <div className="space-y-2">
            {data.map((item, index) => (
              <div key={index} className="p-2 border rounded">
                {JSON.stringify(item)}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

### Form Component Template
```typescript
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface FormData {
  [key: string]: string
}

interface FormComponentProps {
  title: string
  fields: Array<{
    name: string
    label: string
    type: 'text' | 'email' | 'textarea'
    required?: boolean
  }>
  onSubmit: (data: FormData) => Promise<void>
  onSuccess?: () => void
}

export function FormComponent({ title, fields, onSubmit, onSuccess }: FormComponentProps) {
  const [formData, setFormData] = useState<FormData>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleInputChange = (name: string, value: string) => {
    setFormData(prev => ({ ...prev, [name]: value }))
    setError(null)
    setSuccess(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      setIsSubmitting(true)
      setError(null)
      await onSubmit(formData)
      setSuccess(true)
      setFormData({})
      onSuccess?.()
    } catch (error) {
      console.error('Form submission failed:', error)
      setError('Failed to submit form')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-lg font-semibold">{title}</h3>
      
      {fields.map(field => (
        <div key={field.name} className="space-y-2">
          <Label htmlFor={field.name}>
            {field.label}
            {field.required && <span className="text-red-500">*</span>}
          </Label>
          
          {field.type === 'textarea' ? (
            <Textarea
              id={field.name}
              value={formData[field.name] || ''}
              onChange={(e) => handleInputChange(field.name, e.target.value)}
              required={field.required}
            />
          ) : (
            <Input
              id={field.name}
              type={field.type}
              value={formData[field.name] || ''}
              onChange={(e) => handleInputChange(field.name, e.target.value)}
              required={field.required}
            />
          )}
        </div>
      ))}

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded text-red-700">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {success && (
        <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded text-green-700">
          <CheckCircle className="h-4 w-4" />
          Form submitted successfully!
        </div>
      )}

      <Button type="submit" disabled={isSubmitting} className="w-full">
        {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isSubmitting ? 'Submitting...' : 'Submit'}
      </Button>
    </form>
  )
}
```

### Modal Component Template
```typescript
'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'

interface ModalComponentProps {
  trigger: React.ReactNode
  title: string
  description?: string
  children: React.ReactNode
  onConfirm?: () => Promise<void>
  confirmText?: string
  cancelText?: string
}

export function ModalComponent({
  trigger,
  title,
  description,
  children,
  onConfirm,
  confirmText = 'Confirm',
  cancelText = 'Cancel'
}: ModalComponentProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleConfirm = async () => {
    if (!onConfirm) return

    try {
      setIsLoading(true)
      await onConfirm()
      setIsOpen(false)
    } catch (error) {
      console.error('Modal action failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {trigger}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description && (
            <DialogDescription>{description}</DialogDescription>
          )}
        </DialogHeader>
        
        <div className="py-4">
          {children}
        </div>

        {onConfirm && (
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setIsOpen(false)}
              disabled={isLoading}
            >
              {cancelText}
            </Button>
            <Button
              onClick={handleConfirm}
              disabled={isLoading}
            >
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {confirmText}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
```

## Real-time Component Patterns

### WebSocket Subscription Component
```typescript
'use client'

import { useEffect, useState } from 'react'
import { useWebSocket } from '@/lib/websocket'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Wifi, WifiOff } from 'lucide-react'

interface RealtimeComponentProps {
  eventType: string
  title: string
  onEvent?: (data: any) => void
}

export function RealtimeComponent({ eventType, title, onEvent }: RealtimeComponentProps) {
  const { isConnected, subscribe, unsubscribe } = useWebSocket()
  const [events, setEvents] = useState<any[]>([])

  useEffect(() => {
    const handleEvent = (data: any) => {
      setEvents(prev => [data, ...prev.slice(0, 9)]) // Keep last 10 events
      onEvent?.(data)
    }

    const unsubscribeEvent = subscribe(eventType, handleEvent)
    
    return () => {
      unsubscribeEvent()
    }
  }, [eventType, subscribe, onEvent])

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{title}</CardTitle>
        <Badge variant={isConnected ? 'default' : 'destructive'}>
          {isConnected ? (
            <>
              <Wifi className="mr-1 h-3 w-3" />
              Connected
            </>
          ) : (
            <>
              <WifiOff className="mr-1 h-3 w-3" />
              Disconnected
            </>
          )}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {events.length === 0 ? (
            <p className="text-muted-foreground">No events received</p>
          ) : (
            events.map((event, index) => (
              <div key={index} className="p-2 bg-muted rounded text-sm">
                <pre>{JSON.stringify(event, null, 2)}</pre>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
```

## Table Component Patterns

### Data Table with Actions
```typescript
'use client'

import { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { MoreHorizontal, Edit, Trash2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface Column<T> {
  key: keyof T
  label: string
  render?: (value: any, item: T) => React.ReactNode
}

interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  onEdit?: (item: T) => void
  onDelete?: (item: T) => void
  selectable?: boolean
  onSelectionChange?: (selected: T[]) => void
}

export function DataTable<T extends { id: string }>({
  data,
  columns,
  onEdit,
  onDelete,
  selectable = false,
  onSelectionChange
}: DataTableProps<T>) {
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allIds = new Set(data.map(item => item.id))
      setSelectedItems(allIds)
      onSelectionChange?.(data)
    } else {
      setSelectedItems(new Set())
      onSelectionChange?.([])
    }
  }

  const handleSelectItem = (itemId: string, checked: boolean) => {
    const newSelected = new Set(selectedItems)
    if (checked) {
      newSelected.add(itemId)
    } else {
      newSelected.delete(itemId)
    }
    setSelectedItems(newSelected)
    
    const selectedData = data.filter(item => newSelected.has(item.id))
    onSelectionChange?.(selectedData)
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {selectable && (
            <TableHead className="w-12">
              <Checkbox
                checked={selectedItems.size === data.length && data.length > 0}
                onCheckedChange={handleSelectAll}
              />
            </TableHead>
          )}
          {columns.map(column => (
            <TableHead key={String(column.key)}>{column.label}</TableHead>
          ))}
          {(onEdit || onDelete) && (
            <TableHead className="w-12">Actions</TableHead>
          )}
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map(item => (
          <TableRow key={item.id}>
            {selectable && (
              <TableCell>
                <Checkbox
                  checked={selectedItems.has(item.id)}
                  onCheckedChange={(checked) => handleSelectItem(item.id, checked)}
                />
              </TableCell>
            )}
            {columns.map(column => (
              <TableCell key={String(column.key)}>
                {column.render 
                  ? column.render(item[column.key], item)
                  : String(item[column.key])
                }
              </TableCell>
            ))}
            {(onEdit || onDelete) && (
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    {onEdit && (
                      <DropdownMenuItem onClick={() => onEdit(item)}>
                        <Edit className="mr-2 h-4 w-4" />
                        Edit
                      </DropdownMenuItem>
                    )}
                    {onDelete && (
                      <DropdownMenuItem 
                        onClick={() => onDelete(item)}
                        className="text-red-600"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            )}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

## Usage Guidelines

### When to Use Each Pattern

1. **Basic Data Display**: For simple data presentation with refresh capability
2. **Form Component**: For user input forms with validation and submission
3. **Modal Component**: For confirmations, detailed views, or complex interactions
4. **Realtime Component**: For displaying live data updates via WebSocket
5. **Data Table**: For tabular data with sorting, selection, and actions

### Customization Guidelines

- Always extend base patterns rather than creating from scratch
- Maintain consistent prop naming across similar components
- Use TypeScript generics for reusable components
- Follow the established error handling patterns
- Implement proper loading states for all async operations 