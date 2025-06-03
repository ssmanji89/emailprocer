'use client'

import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { apiClient } from '@/lib/api-client'
import { Escalation } from '@/types/api'
import { formatDate, debounce, getLocalStorageItem, setLocalStorageItem } from '@/lib/utils'
import {
  Search,
  Filter,
  X,
  Calendar as CalendarIcon,
  Save,
  Bookmark,
  Trash2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Settings,
  Clock,
  User,
  Tag,
  AlertTriangle,
  Download
} from 'lucide-react'

interface SearchFilters {
  query: string
  status: string[]
  priority: string[]
  team: string[]
  assignee: string[]
  dateRange: {
    from: Date | null
    to: Date | null
  }
  slaStatus: string[]
  escalationReason: string[]
  emailDomain: string[]
  confidenceRange: {
    min: number
    max: number
  }
}

interface SavedSearch {
  id: string
  name: string
  filters: SearchFilters
  createdAt: string
}

interface AdvancedSearchFilterProps {
  onFiltersChange: (filters: SearchFilters) => void
  onSearch: (query: string, filters: Omit<SearchFilters, 'query'>) => void
  totalResults?: number
  isLoading?: boolean
}

const defaultFilters: SearchFilters = {
  query: '',
  status: [],
  priority: [],
  team: [],
  assignee: [],
  dateRange: { from: null, to: null },
  slaStatus: [],
  escalationReason: [],
  emailDomain: [],
  confidenceRange: { min: 0, max: 100 }
}

export function AdvancedSearchFilter({
  onFiltersChange,
  onSearch,
  totalResults = 0,
  isLoading = false
}: AdvancedSearchFilterProps) {
  const [filters, setFilters] = useState<SearchFilters>(defaultFilters)
  const [isExpanded, setIsExpanded] = useState(false)
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([])
  const [saveSearchName, setSaveSearchName] = useState('')
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [availableOptions, setAvailableOptions] = useState({
    teams: [] as string[],
    assignees: [] as string[],
    escalationReasons: [] as string[],
    emailDomains: [] as string[]
  })

  // Load saved searches and available options on component mount
  useEffect(() => {
    const saved = getLocalStorageItem<SavedSearch[]>('escalation-saved-searches', [])
    setSavedSearches(saved)
    loadAvailableOptions()
  }, [])

  // Debounced search function
  const debouncedSearch = useMemo(
    () => debounce((searchFilters: SearchFilters) => {
      onSearch(searchFilters.query, {
        status: searchFilters.status,
        priority: searchFilters.priority,
        team: searchFilters.team,
        assignee: searchFilters.assignee,
        dateRange: searchFilters.dateRange,
        slaStatus: searchFilters.slaStatus,
        escalationReason: searchFilters.escalationReason,
        emailDomain: searchFilters.emailDomain,
        confidenceRange: searchFilters.confidenceRange
      })
    }, 300),
    [onSearch]
  )

  // Trigger search when filters change
  useEffect(() => {
    onFiltersChange(filters)
    debouncedSearch(filters)
  }, [filters, onFiltersChange, debouncedSearch])

  const loadAvailableOptions = async () => {
    try {
      // In a real implementation, these would come from API endpoints
      // For now, using placeholder data
      setAvailableOptions({
        teams: ['Support Team', 'Technical Team', 'Management Team', 'QA Team'],
        assignees: ['John Doe', 'Jane Smith', 'Mike Johnson', 'Sarah Wilson'],
        escalationReasons: [
          'Classification Error',
          'Processing Delay',
          'Customer Complaint',
          'Technical Issue',
          'Policy Violation',
          'Urgent Request'
        ],
        emailDomains: ['gmail.com', 'company.com', 'outlook.com', 'yahoo.com']
      })
    } catch (error) {
      console.error('Failed to load filter options:', error)
    }
  }

  const updateFilter = <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const toggleArrayFilter = (key: keyof SearchFilters, value: string) => {
    const currentArray = filters[key] as string[]
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value]
    updateFilter(key, newArray)
  }

  const clearAllFilters = () => {
    setFilters(defaultFilters)
  }

  const getActiveFilterCount = () => {
    let count = 0
    if (filters.query) count++
    if (filters.status.length > 0) count++
    if (filters.priority.length > 0) count++
    if (filters.team.length > 0) count++
    if (filters.assignee.length > 0) count++
    if (filters.dateRange.from || filters.dateRange.to) count++
    if (filters.slaStatus.length > 0) count++
    if (filters.escalationReason.length > 0) count++
    if (filters.emailDomain.length > 0) count++
    if (filters.confidenceRange.min > 0 || filters.confidenceRange.max < 100) count++
    return count
  }

  const saveCurrentSearch = () => {
    if (!saveSearchName.trim()) return

    const newSearch: SavedSearch = {
      id: Date.now().toString(),
      name: saveSearchName,
      filters: { ...filters },
      createdAt: new Date().toISOString()
    }

    const updatedSearches = [...savedSearches, newSearch]
    setSavedSearches(updatedSearches)
    setLocalStorageItem('escalation-saved-searches', updatedSearches)
    setSaveSearchName('')
    setShowSaveDialog(false)
  }

  const loadSavedSearch = (search: SavedSearch) => {
    setFilters(search.filters)
  }

  const deleteSavedSearch = (searchId: string) => {
    const updatedSearches = savedSearches.filter(s => s.id !== searchId)
    setSavedSearches(updatedSearches)
    setLocalStorageItem('escalation-saved-searches', updatedSearches)
  }

  const exportFilters = () => {
    const filterData = {
      filters,
      timestamp: new Date().toISOString(),
      totalResults
    }
    
    const blob = new Blob([JSON.stringify(filterData, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `escalation-search-filters-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Advanced Search & Filters
            {getActiveFilterCount() > 0 && (
              <Badge variant="secondary">
                {getActiveFilterCount()} active
              </Badge>
            )}
          </CardTitle>
          <div className="flex gap-2">
            <span className="text-sm text-gray-600">
              {totalResults} results
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Basic Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search escalations by subject, sender, content..."
            value={filters.query}
            onChange={(e) => updateFilter('query', e.target.value)}
            className="pl-10 pr-10"
          />
          {filters.query && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
              onClick={() => updateFilter('query', '')}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>

        {/* Quick Filters */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant={filters.status.includes('open') ? 'default' : 'outline'}
            size="sm"
            onClick={() => toggleArrayFilter('status', 'open')}
          >
            Open
          </Button>
          <Button
            variant={filters.priority.includes('critical') ? 'destructive' : 'outline'}
            size="sm"
            onClick={() => toggleArrayFilter('priority', 'critical')}
          >
            Critical
          </Button>
          <Button
            variant={filters.slaStatus.includes('overdue') ? 'destructive' : 'outline'}
            size="sm"
            onClick={() => toggleArrayFilter('slaStatus', 'overdue')}
          >
            Overdue
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => updateFilter('dateRange', {
              from: new Date(Date.now() - 24 * 60 * 60 * 1000),
              to: new Date()
            })}
          >
            Last 24h
          </Button>
        </div>

        {/* Advanced Filters (Collapsible) */}
        {isExpanded && (
          <div className="space-y-6 pt-4 border-t">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Status Filter */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Status
                </Label>
                <div className="space-y-2">
                  {['open', 'in_progress', 'resolved', 'closed'].map((status) => (
                    <div key={status} className="flex items-center space-x-2">
                      <Checkbox
                        checked={filters.status.includes(status)}
                        onCheckedChange={() => toggleArrayFilter('status', status)}
                      />
                      <label className="text-sm capitalize">{status.replace('_', ' ')}</label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Priority Filter */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Tag className="h-4 w-4" />
                  Priority
                </Label>
                <div className="space-y-2">
                  {['low', 'medium', 'high', 'critical'].map((priority) => (
                    <div key={priority} className="flex items-center space-x-2">
                      <Checkbox
                        checked={filters.priority.includes(priority)}
                        onCheckedChange={() => toggleArrayFilter('priority', priority)}
                      />
                      <label className="text-sm capitalize">{priority}</label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Team Filter */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Team
                </Label>
                <div className="space-y-2">
                  {availableOptions.teams.map((team) => (
                    <div key={team} className="flex items-center space-x-2">
                      <Checkbox
                        checked={filters.team.includes(team)}
                        onCheckedChange={() => toggleArrayFilter('team', team)}
                      />
                      <label className="text-sm">{team}</label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Date Range Filter */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <CalendarIcon className="h-4 w-4" />
                  Date Range
                </Label>
                <div className="flex gap-2">
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" size="sm" className="flex-1">
                        {filters.dateRange.from ? formatDate(filters.dateRange.from) : 'From'}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={filters.dateRange.from || undefined}
                        onSelect={(date) => updateFilter('dateRange', { ...filters.dateRange, from: date || null })}
                      />
                    </PopoverContent>
                  </Popover>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" size="sm" className="flex-1">
                        {filters.dateRange.to ? formatDate(filters.dateRange.to) : 'To'}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={filters.dateRange.to || undefined}
                        onSelect={(date) => updateFilter('dateRange', { ...filters.dateRange, to: date || null })}
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>

              {/* SLA Status Filter */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  SLA Status
                </Label>
                <div className="space-y-2">
                  {['on_time', 'warning', 'overdue'].map((status) => (
                    <div key={status} className="flex items-center space-x-2">
                      <Checkbox
                        checked={filters.slaStatus.includes(status)}
                        onCheckedChange={() => toggleArrayFilter('slaStatus', status)}
                      />
                      <label className="text-sm capitalize">{status.replace('_', ' ')}</label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Escalation Reason Filter */}
              <div className="space-y-2">
                <Label>Escalation Reason</Label>
                <Select value="" onValueChange={(value) => toggleArrayFilter('escalationReason', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select reasons" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableOptions.escalationReasons.map((reason) => (
                      <SelectItem key={reason} value={reason}>
                        {reason}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <div className="flex flex-wrap gap-1">
                  {filters.escalationReason.map((reason) => (
                    <Badge key={reason} variant="secondary" className="text-xs">
                      {reason}
                      <X 
                        className="h-3 w-3 ml-1 cursor-pointer" 
                        onClick={() => toggleArrayFilter('escalationReason', reason)}
                      />
                    </Badge>
                  ))}
                </div>
              </div>
            </div>

            {/* Confidence Range */}
            <div className="space-y-2">
              <Label>Confidence Range: {filters.confidenceRange.min}% - {filters.confidenceRange.max}%</Label>
              <div className="flex gap-4 items-center">
                <Input
                  type="range"
                  min="0"
                  max="100"
                  value={filters.confidenceRange.min}
                  onChange={(e) => updateFilter('confidenceRange', {
                    ...filters.confidenceRange,
                    min: parseInt(e.target.value)
                  })}
                  className="flex-1"
                />
                <Input
                  type="range"
                  min="0"
                  max="100"
                  value={filters.confidenceRange.max}
                  onChange={(e) => updateFilter('confidenceRange', {
                    ...filters.confidenceRange,
                    max: parseInt(e.target.value)
                  })}
                  className="flex-1"
                />
              </div>
            </div>
          </div>
        )}

        {/* Saved Searches */}
        {savedSearches.length > 0 && (
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Bookmark className="h-4 w-4" />
              Saved Searches
            </Label>
            <div className="flex flex-wrap gap-2">
              {savedSearches.map((search) => (
                <div key={search.id} className="flex items-center gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadSavedSearch(search)}
                    className="text-xs"
                  >
                    {search.name}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteSavedSearch(search.id)}
                    className="h-6 w-6 p-0 text-red-600 hover:text-red-800"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-4 border-t">
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={clearAllFilters}
              disabled={getActiveFilterCount() === 0}
            >
              Clear All
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSaveDialog(true)}
              disabled={getActiveFilterCount() === 0}
            >
              <Save className="h-3 w-3 mr-1" />
              Save Search
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={exportFilters}
            >
              <Download className="h-3 w-3 mr-1" />
              Export
            </Button>
          </div>
          
          {isLoading && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <RefreshCw className="h-3 w-3 animate-spin" />
              Searching...
            </div>
          )}
        </div>

        {/* Save Search Dialog */}
        {showSaveDialog && (
          <div className="p-4 border rounded-lg bg-gray-50">
            <div className="space-y-3">
              <Label>Save Current Search</Label>
              <Input
                placeholder="Enter search name..."
                value={saveSearchName}
                onChange={(e) => setSaveSearchName(e.target.value)}
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={saveCurrentSearch}
                  disabled={!saveSearchName.trim()}
                >
                  Save
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowSaveDialog(false)
                    setSaveSearchName('')
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 