'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Card, CardContent } from '@/components/ui/card'
import { EmailHistoryParams } from '@/types/api'
import { Search, X, Calendar } from 'lucide-react'

interface EmailSearchFormProps {
  onSearch: (filters: EmailHistoryParams) => void
  initialFilters: EmailHistoryParams
  isLoading?: boolean
}

const DATE_PRESETS = [
  { label: 'Today', value: '1' },
  { label: 'Last 7 days', value: '7' },
  { label: 'Last 30 days', value: '30' },
  { label: 'Last 90 days', value: '90' },
  { label: 'Custom', value: 'custom' },
]

const STATUS_OPTIONS = [
  { label: 'All Status', value: '' },
  { label: 'Completed', value: 'completed' },
  { label: 'Processing', value: 'processing' },
  { label: 'Failed', value: 'failed' },
  { label: 'Pending', value: 'pending' },
]

const CATEGORY_OPTIONS = [
  { label: 'All Categories', value: '' },
  { label: 'Support Request', value: 'support' },
  { label: 'Sales Inquiry', value: 'sales' },
  { label: 'Complaint', value: 'complaint' },
  { label: 'General Inquiry', value: 'general' },
  { label: 'Spam', value: 'spam' },
]

export function EmailSearchForm({ onSearch, initialFilters, isLoading = false }: EmailSearchFormProps) {
  const [filters, setFilters] = useState<EmailHistoryParams>(initialFilters)
  const [datePreset, setDatePreset] = useState('30')
  const [showAdvanced, setShowAdvanced] = useState(false)

  useEffect(() => {
    setFilters(initialFilters)
  }, [initialFilters])

  const handleFilterChange = (field: keyof EmailHistoryParams, value: string | number | undefined) => {
    setFilters(prev => ({
      ...prev,
      [field]: value === '' ? undefined : value,
    }))
  }

  const handleDatePresetChange = (value: string) => {
    setDatePreset(value)
    if (value === 'custom') {
      // Don't change the filters, let user set custom dates
      return
    }
    
    const days = parseInt(value)
    handleFilterChange('days', days)
    handleFilterChange('date_from', undefined)
    handleFilterChange('date_to', undefined)
  }

  const handleSearch = () => {
    onSearch(filters)
  }

  const handleClear = () => {
    const clearedFilters: EmailHistoryParams = {
      limit: filters.limit,
      page: 1,
    }
    setFilters(clearedFilters)
    setDatePreset('30')
    onSearch(clearedFilters)
  }

  const hasActiveFilters = Object.entries(filters).some(
    ([key, value]) => key !== 'limit' && key !== 'page' && value !== undefined && value !== ''
  )

  return (
    <div className="space-y-4">
      {/* Basic Search Fields */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="sender">Sender Email</Label>
          <Input
            id="sender"
            placeholder="sender@example.com"
            value={filters.sender || ''}
            onChange={(e) => handleFilterChange('sender', e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="subject">Subject</Label>
          <Input
            id="subject"
            placeholder="Email subject..."
            value={filters.subject || ''}
            onChange={(e) => handleFilterChange('subject', e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="category">Category</Label>
          <Select
            id="category"
            value={filters.category || ''}
            onChange={(e) => handleFilterChange('category', e.target.value)}
          >
            <option value="">All Categories</option>
            {CATEGORY_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {/* Date Range and Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="date-preset">Date Range</Label>
          <Select
            id="date-preset"
            value={datePreset}
            onChange={(e) => handleDatePresetChange(e.target.value)}
          >
            {DATE_PRESETS.map(preset => (
              <option key={preset.value} value={preset.value}>
                {preset.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="status">Processing Status</Label>
          <Select
            id="status"
            value={filters.status || ''}
            onChange={(e) => handleFilterChange('status', e.target.value)}
          >
            {STATUS_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="flex items-end">
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Filters
          </Button>
        </div>
      </div>

      {/* Advanced Filters */}
      {showAdvanced && (
        <Card>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="content">Email Content</Label>
                <Input
                  id="content"
                  placeholder="Search in email content..."
                  value={filters.content || ''}
                  onChange={(e) => handleFilterChange('content', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Confidence Range</Label>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    placeholder="Min %"
                    value={filters.confidence_min !== undefined ? filters.confidence_min * 100 : ''}
                    onChange={(e) => {
                      const value = e.target.value
                      handleFilterChange('confidence_min', value ? parseFloat(value) / 100 : undefined)
                    }}
                  />
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    placeholder="Max %"
                    value={filters.confidence_max !== undefined ? filters.confidence_max * 100 : ''}
                    onChange={(e) => {
                      const value = e.target.value
                      handleFilterChange('confidence_max', value ? parseFloat(value) / 100 : undefined)
                    }}
                  />
                </div>
              </div>

              {datePreset === 'custom' && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="date-from">From Date</Label>
                    <Input
                      id="date-from"
                      type="date"
                      value={filters.date_from || ''}
                      onChange={(e) => handleFilterChange('date_from', e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="date-to">To Date</Label>
                    <Input
                      id="date-to"
                      type="date"
                      value={filters.date_to || ''}
                      onChange={(e) => handleFilterChange('date_to', e.target.value)}
                    />
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <Button
            onClick={handleSearch}
            disabled={isLoading}
            className="flex items-center gap-2"
          >
            <Search className="h-4 w-4" />
            {isLoading ? 'Searching...' : 'Search'}
          </Button>
          
          {hasActiveFilters && (
            <Button
              variant="outline"
              onClick={handleClear}
              className="flex items-center gap-2"
            >
              <X className="h-4 w-4" />
              Clear All
            </Button>
          )}
        </div>

        <div className="text-sm text-muted-foreground">
          {hasActiveFilters && (
            <span>Active filters applied</span>
          )}
        </div>
      </div>
    </div>
  )
} 