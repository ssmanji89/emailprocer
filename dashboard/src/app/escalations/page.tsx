'use client'

import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

import { EscalationsGrid } from '@/components/dashboard/escalations-grid'
import { SLAAlerts } from '@/components/alerts/sla-alerts'
import { TeamWorkloadChart } from '@/components/charts/team-workload-chart'
// import { EscalationDetailModal } from '@/components/modals/escalation-detail-modal'
import { apiClient } from '@/lib/api-client'
// import { Escalation } from '@/types/api'
import { formatNumber, formatDuration } from '@/lib/utils'
import { 
  AlertTriangle, 
  Users, 
  RefreshCw,
  Filter
} from 'lucide-react'

export default function EscalationsPage() {
  // const [selectedEscalation, setSelectedEscalation] = useState<Escalation | null>(null)
  // const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [priorityFilter, setPriorityFilter] = useState<string>('all')

  const { data: escalations, isLoading, error, refetch } = useQuery({
    queryKey: ['escalations', statusFilter, priorityFilter],
    queryFn: () => apiClient.getActiveEscalations(),
    refetchInterval: 10000, // Refresh every 10 seconds for real-time updates
  })

  const { data: teamPerformance } = useQuery({
    queryKey: ['team-performance'],
    queryFn: () => apiClient.getTeamPerformance('all', '7d'),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // const handleEscalationSelect = (escalation: Escalation) => {
  //   setSelectedEscalation(escalation)
  //   setIsDetailModalOpen(true)
  // }

  const summaryStats = useMemo(() => {
    if (!escalations) return null

    const totalActive = escalations.length
    const overdue = escalations.filter(e => new Date(e.sla_due_at) < new Date()).length
    const resolvedToday = escalations.filter(e => 
      e.status === 'resolved' && 
      new Date(e.resolved_at || '').toDateString() === new Date().toDateString()
    ).length
    
    const avgResolutionTime = escalations
      .filter(e => e.status === 'resolved' && e.resolved_at && e.created_at)
      .reduce((acc, e) => {
        const created = new Date(e.created_at).getTime()
        const resolved = new Date(e.resolved_at!).getTime()
        return acc + (resolved - created) / (1000 * 60 * 60) // hours
      }, 0) / escalations.filter(e => e.status === 'resolved').length || 0

    return {
      totalActive,
      overdue,
      resolvedToday,
      avgResolutionTime,
      slaCompliance: totalActive > 0 ? ((totalActive - overdue) / totalActive) * 100 : 100,
    }
  }, [escalations])

  const filteredEscalations = useMemo(() => {
    if (!escalations) return []
    
    return escalations.filter(escalation => {
      const statusMatch = statusFilter === 'all' || escalation.status === statusFilter
      const priorityMatch = priorityFilter === 'all' || escalation.priority === priorityFilter
      return statusMatch && priorityMatch
    })
  }, [escalations, statusFilter, priorityFilter])

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-4" />
          <p className="text-red-500">Failed to load escalations</p>
          <p className="text-sm text-muted-foreground mt-2">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <Button onClick={() => refetch()} className="mt-4">
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Escalation Management</h1>
          <p className="text-muted-foreground">
            Monitor and resolve active escalations with team assignment and SLA tracking
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refetch()}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Statistics */}
      {summaryStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Active</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(summaryStats.totalActive)}
              </div>
              <p className="text-xs text-muted-foreground">
                Open escalations
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {formatNumber(summaryStats.overdue)}
              </div>
              <p className="text-xs text-muted-foreground">
                Past SLA deadline
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Resolved Today</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {formatNumber(summaryStats.resolvedToday)}
              </div>
              <p className="text-xs text-muted-foreground">
                Completed today
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Avg Resolution Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatDuration(summaryStats.avgResolutionTime * 3600)}
              </div>
              <p className="text-xs text-muted-foreground">
                Average time to resolve
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">SLA Compliance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {summaryStats.slaCompliance.toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                On-time resolution rate
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* SLA Alerts */}
      <SLAAlerts escalations={filteredEscalations} />

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="all">All Status</option>
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Priority</label>
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="all">All Priorities</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Team Workload Chart */}
      {teamPerformance && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Team Workload Distribution
            </CardTitle>
            <CardDescription>
              Current escalation assignments and team capacity
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TeamWorkloadChart data={teamPerformance} />
          </CardContent>
        </Card>
      )}

      {/* Escalations Grid */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Active Escalations
            {filteredEscalations && (
              <span className="text-sm font-normal text-muted-foreground">
                ({formatNumber(filteredEscalations.length)} total)
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EscalationsGrid
            escalations={filteredEscalations}
            isLoading={isLoading}
            onEscalationSelect={() => {}}
            onRefetch={refetch}
          />
        </CardContent>
      </Card>

      {/* Escalation Detail Modal */}
      {/* {selectedEscalation && (
        <EscalationDetailModal
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false)
            setSelectedEscalation(null)
          }}
          escalation={selectedEscalation}
          onRefetch={refetch}
        />
      )} */}
    </div>
  )
} 