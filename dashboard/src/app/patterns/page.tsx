'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Search, TrendingUp, Clock, CheckCircle, XCircle, Eye, Download, Calculator } from 'lucide-react'
import Link from 'next/link'
import { apiClient } from '@/lib/api-client'
import { PatternParams } from '@/types/api'
import { PatternDetailModal } from '@/components/modals/pattern-detail-modal'

export default function PatternsPage() {
  const [filters, setFilters] = useState<PatternParams>({
    min_frequency: 5,
    min_automation_potential: 70.0,
  })
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPattern, setSelectedPattern] = useState<any>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['patterns', filters],
    queryFn: () => apiClient.getPatternAnalytics(filters),
    refetchInterval: 30000,
  })

  const filteredPatterns = data?.automation_candidates?.filter(pattern =>
    pattern.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    pattern.pattern_type.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  const handleApprove = async (patternId: string) => {
    try {
      await apiClient.approvePattern(patternId)
      refetch() // Refresh the data
    } catch (error) {
      console.error('Error approving pattern:', error)
    }
  }

  const handleReject = async (patternId: string) => {
    try {
      await apiClient.rejectPattern(patternId)
      refetch() // Refresh the data
    } catch (error) {
      console.error('Error rejecting pattern:', error)
    }
  }

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Exporting patterns data')
  }

  const getAutomationPotentialColor = (potential: number) => {
    if (potential >= 90) return 'bg-green-100 text-green-800'
    if (potential >= 75) return 'bg-blue-100 text-blue-800'
    if (potential >= 60) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  const formatTimeSavings = (minutes: number) => {
    if (minutes >= 60) {
      return `${(minutes / 60).toFixed(1)}h`
    }
    return `${minutes}m`
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-2 text-sm text-muted-foreground">Loading patterns...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-red-600">
            <p>Error loading patterns: {error.message}</p>
            <Button onClick={() => refetch()} variant="outline" className="mt-2">
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Pattern Management</h1>
          <p className="text-muted-foreground">
            Identify and manage automation opportunities in email patterns
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Link href="/patterns/roi-calculator">
            <Button>
              <Calculator className="h-4 w-4 mr-2" />
              ROI Calculator
            </Button>
          </Link>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Patterns</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{filteredPatterns.length}</div>
            <p className="text-xs text-muted-foreground">
              Automation candidates identified
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Potential</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {filteredPatterns.filter(p => p.automation_potential >= 90).length}
            </div>
            <p className="text-xs text-muted-foreground">
              90%+ automation potential
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Time Savings</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatTimeSavings(
                filteredPatterns.reduce((sum, p) => sum + p.time_savings_potential_minutes, 0)
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Total potential savings
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>
            Refine the automation candidates based on your criteria
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="search">Search</Label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="search"
                  placeholder="Search patterns..."
                  className="pl-8"
                  value={searchTerm}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="frequency">Min Frequency</Label>
              <Input
                id="frequency"
                type="number"
                min="1"
                value={filters.min_frequency}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFilters(prev => ({
                  ...prev,
                  min_frequency: parseInt(e.target.value) || 1
                }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="potential">Min Automation %</Label>
              <Input
                id="potential"
                type="number"
                min="0"
                max="100"
                value={filters.min_automation_potential}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFilters(prev => ({
                  ...prev,
                  min_automation_potential: parseFloat(e.target.value) || 0
                }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Actions</Label>
              <Button onClick={() => refetch()} variant="outline" className="w-full">
                Refresh Data
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Patterns Table */}
      <Card>
        <CardHeader>
          <CardTitle>Automation Candidates</CardTitle>
          <CardDescription>
            Identified patterns with automation potential and time savings analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Pattern Type</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Frequency</TableHead>
                  <TableHead>Automation Potential</TableHead>
                  <TableHead>Time Savings</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPatterns.map((pattern) => (
                  <TableRow key={pattern.pattern_id}>
                    <TableCell>
                      <Badge variant="outline">{pattern.pattern_type}</Badge>
                    </TableCell>
                    <TableCell className="max-w-md">
                      <div className="truncate" title={pattern.description}>
                        {pattern.description}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <span className="font-medium">{pattern.frequency}</span>
                        <span className="text-sm text-muted-foreground">emails</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge 
                        className={getAutomationPotentialColor(pattern.automation_potential)}
                      >
                        {pattern.automation_potential.toFixed(1)}%
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        <span className="font-medium">
                          {formatTimeSavings(pattern.time_savings_potential_minutes)}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedPattern(pattern)
                            setIsModalOpen(true)
                          }}
                        >
                          <Eye className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleApprove(pattern.pattern_id)}
                        >
                          <CheckCircle className="h-3 w-3 text-green-600" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleReject(pattern.pattern_id)}
                        >
                          <XCircle className="h-3 w-3 text-red-600" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          
          {filteredPatterns.length === 0 && (
            <div className="text-center py-8">
              <p className="text-muted-foreground">
                No patterns found matching your criteria. Try adjusting the filters.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pattern Detail Modal */}
      {selectedPattern && (
        <PatternDetailModal
          pattern={selectedPattern}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false)
            setSelectedPattern(null)
          }}
          onApprove={(patternId) => {
            handleApprove(patternId)
            setIsModalOpen(false)
            setSelectedPattern(null)
          }}
          onReject={(patternId) => {
            handleReject(patternId)
            setIsModalOpen(false)
            setSelectedPattern(null)
          }}
        />
      )}
    </div>
  )
} 