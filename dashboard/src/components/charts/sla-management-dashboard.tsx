'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { apiClient } from '@/lib/api-client'
import { Escalation } from '@/types/api'
import { 
  formatDuration, 
  formatPercentage, 
  formatTimeAgo, 
  formatRelativeTime,
  getStatusColor,
  formatNumber
} from '@/lib/utils'
import {
  Clock,
  AlertTriangle,
  Target,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  XCircle,
  Timer,
  Calendar,
  BarChart3,
  RefreshCw,
  Settings,
  Download,
  Bell,
  Loader2,
  Activity,
  Users,
  Gauge
} from 'lucide-react'

interface SLAMetrics {
  totalEscalations: number
  onTimeCompletions: number
  overdueEscalations: number
  warningEscalations: number
  averageResolutionTime: number
  complianceRate: number
  breachRate: number
  responseTimeCompliance: number
}

interface SLABreach {
  escalationId: string
  subject: string
  priority: string
  breachType: 'response' | 'resolution'
  breachTime: string
  timeOverdue: number
  assignedTo?: string
}

interface SLAPerformance {
  period: string
  complianceRate: number
  averageResponseTime: number
  averageResolutionTime: number
  totalEscalations: number
  breaches: number
}

interface SLATarget {
  priority: string
  responseTimeTarget: number // in seconds
  resolutionTimeTarget: number // in seconds
}

const SLA_TARGETS: SLATarget[] = [
  { priority: 'critical', responseTimeTarget: 900, resolutionTimeTarget: 14400 }, // 15 min, 4 hours
  { priority: 'high', responseTimeTarget: 1800, resolutionTimeTarget: 28800 }, // 30 min, 8 hours
  { priority: 'medium', responseTimeTarget: 3600, resolutionTimeTarget: 86400 }, // 1 hour, 24 hours
  { priority: 'low', responseTimeTarget: 7200, resolutionTimeTarget: 172800 }, // 2 hours, 48 hours
]

interface SLAManagementDashboardProps {
  period?: string
  teamId?: string
}

export function SLAManagementDashboard({
  period = '7d',
  teamId = 'all'
}: SLAManagementDashboardProps) {
  const [metrics, setMetrics] = useState<SLAMetrics | null>(null)
  const [breaches, setBreaches] = useState<SLABreach[]>([])
  const [performance, setPerformance] = useState<SLAPerformance[]>([])
  const [escalations, setEscalations] = useState<Escalation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedPeriod, setSelectedPeriod] = useState(period)
  const [selectedTeam, setSelectedTeam] = useState(teamId)
  const [viewMode, setViewMode] = useState<'overview' | 'detailed' | 'breaches'>('overview')

  useEffect(() => {
    loadSLAData()
  }, [selectedPeriod, selectedTeam])

  const loadSLAData = async () => {
    setIsLoading(true)
    try {
      // In a real implementation, these would be separate API endpoints
      const [escalationData] = await Promise.all([
        apiClient.getActiveEscalations()
      ])
      
      setEscalations(escalationData)
      calculateSLAMetrics(escalationData)
      identifyBreaches(escalationData)
      generatePerformanceData(escalationData)
    } catch (error) {
      console.error('Failed to load SLA data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const calculateSLAMetrics = (escalationData: Escalation[]) => {
    const now = new Date()
    let onTime = 0
    let overdue = 0
    let warning = 0
    let totalResolutionTime = 0
    let resolvedCount = 0

    escalationData.forEach(escalation => {
      const target = SLA_TARGETS.find(t => t.priority === escalation.priority)
      if (!target) return

      const createdAt = new Date(escalation.created_at)
      const dueAt = new Date(escalation.sla_due_at)
      const timeElapsed = now.getTime() - createdAt.getTime()
      const timeToDue = dueAt.getTime() - now.getTime()

      // Check SLA status
      if (escalation.status === 'resolved' || escalation.status === 'closed') {
        resolvedCount++
        const resolutionTime = new Date(escalation.updated_at).getTime() - createdAt.getTime()
        totalResolutionTime += resolutionTime
        
        if (resolutionTime <= target.resolutionTimeTarget * 1000) {
          onTime++
        }
      } else {
        // Active escalation
        if (timeToDue < 0) {
          overdue++
        } else if (timeToDue < target.resolutionTimeTarget * 1000 * 0.2) { // 20% of target time remaining
          warning++
        }
      }
    })

    const avgResolutionTime = resolvedCount > 0 ? totalResolutionTime / resolvedCount : 0
    const complianceRate = escalationData.length > 0 ? (onTime / escalationData.length) * 100 : 0
    const breachRate = escalationData.length > 0 ? (overdue / escalationData.length) * 100 : 0

    setMetrics({
      totalEscalations: escalationData.length,
      onTimeCompletions: onTime,
      overdueEscalations: overdue,
      warningEscalations: warning,
      averageResolutionTime: avgResolutionTime / 1000, // Convert to seconds
      complianceRate,
      breachRate,
      responseTimeCompliance: 95 // Placeholder
    })
  }

  const identifyBreaches = (escalationData: Escalation[]) => {
    const now = new Date()
    const slaBreaches: SLABreach[] = []

    escalationData.forEach(escalation => {
      const target = SLA_TARGETS.find(t => t.priority === escalation.priority)
      if (!target) return

      const dueAt = new Date(escalation.sla_due_at)
      const timeToDue = dueAt.getTime() - now.getTime()

      if (timeToDue < 0 && (escalation.status === 'open' || escalation.status === 'in_progress')) {
        slaBreaches.push({
          escalationId: escalation.escalation_id,
          subject: escalation.email_subject,
          priority: escalation.priority,
          breachType: 'resolution',
          breachTime: dueAt.toISOString(),
          timeOverdue: Math.abs(timeToDue),
          assignedTo: escalation.assigned_to
        })
      }
    })

    setBreaches(slaBreaches)
  }

  const generatePerformanceData = (escalationData: Escalation[]) => {
    // Generate mock performance data for different periods
    const performanceData: SLAPerformance[] = [
      {
        period: 'Today',
        complianceRate: 92,
        averageResponseTime: 1200,
        averageResolutionTime: 18000,
        totalEscalations: 15,
        breaches: 1
      },
      {
        period: 'Yesterday',
        complianceRate: 88,
        averageResponseTime: 1800,
        averageResolutionTime: 22000,
        totalEscalations: 23,
        breaches: 3
      },
      {
        period: 'Last 7 days',
        complianceRate: 85,
        averageResponseTime: 1600,
        averageResolutionTime: 20000,
        totalEscalations: 156,
        breaches: 12
      },
      {
        period: 'Last 30 days',
        complianceRate: 87,
        averageResponseTime: 1500,
        averageResolutionTime: 19500,
        totalEscalations: 642,
        breaches: 45
      }
    ]

    setPerformance(performanceData)
  }

  const getSLAStatusColor = (status: 'ontime' | 'warning' | 'overdue') => {
    switch (status) {
      case 'ontime': return 'bg-green-100 text-green-800'
      case 'warning': return 'bg-yellow-100 text-yellow-800'
      case 'overdue': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getComplianceStatus = (rate: number) => {
    if (rate >= 95) return { status: 'excellent', color: 'text-green-600', icon: <CheckCircle className="h-4 w-4" /> }
    if (rate >= 85) return { status: 'good', color: 'text-blue-600', icon: <Target className="h-4 w-4" /> }
    if (rate >= 70) return { status: 'needs improvement', color: 'text-yellow-600', icon: <AlertTriangle className="h-4 w-4" /> }
    return { status: 'critical', color: 'text-red-600', icon: <XCircle className="h-4 w-4" /> }
  }

  const exportSLAReport = () => {
    const reportData = {
      generatedAt: new Date().toISOString(),
      period: selectedPeriod,
      team: selectedTeam,
      metrics,
      breaches,
      performance
    }
    
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `sla-report-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            SLA Management Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin mr-2" />
            <span>Loading SLA data...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  const complianceStatus = metrics ? getComplianceStatus(metrics.complianceRate) : null

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              SLA Management Dashboard
              {complianceStatus && (
                <Badge className={`${complianceStatus.color} bg-transparent border-current`}>
                  {complianceStatus.icon}
                  {formatPercentage(metrics?.complianceRate || 0)} compliance
                </Badge>
              )}
            </CardTitle>
            <div className="flex gap-2">
              <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1d">Last 24h</SelectItem>
                  <SelectItem value="7d">Last 7 days</SelectItem>
                  <SelectItem value="30d">Last 30 days</SelectItem>
                  <SelectItem value="90d">Last 90 days</SelectItem>
                </SelectContent>
              </Select>
              <Select value={viewMode} onValueChange={(value: any) => setViewMode(value)}>
                <SelectTrigger className="w-36">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="overview">Overview</SelectItem>
                  <SelectItem value="detailed">Detailed</SelectItem>
                  <SelectItem value="breaches">Breaches</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="sm"
                onClick={loadSLAData}
                disabled={isLoading}
              >
                <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={exportSLAReport}
              >
                <Download className="h-3 w-3 mr-1" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Overview Metrics */}
      {(viewMode === 'overview' || viewMode === 'detailed') && metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">SLA Compliance</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatPercentage(metrics.complianceRate)}
                  </p>
                </div>
                <div className="p-2 bg-green-100 rounded-full">
                  <Target className="h-6 w-6 text-green-600" />
                </div>
              </div>
              <Progress value={metrics.complianceRate} className="mt-3" />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Overdue</p>
                  <p className="text-2xl font-bold text-red-600">
                    {metrics.overdueEscalations}
                  </p>
                </div>
                <div className="p-2 bg-red-100 rounded-full">
                  <XCircle className="h-6 w-6 text-red-600" />
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {formatPercentage(metrics.breachRate)} breach rate
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Warning Zone</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {metrics.warningEscalations}
                  </p>
                </div>
                <div className="p-2 bg-yellow-100 rounded-full">
                  <AlertTriangle className="h-6 w-6 text-yellow-600" />
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Approaching deadline
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Resolution</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatDuration(metrics.averageResolutionTime)}
                  </p>
                </div>
                <div className="p-2 bg-blue-100 rounded-full">
                  <Timer className="h-6 w-6 text-blue-600" />
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Resolution time
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* SLA Targets by Priority */}
      {viewMode === 'detailed' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">SLA Targets by Priority</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {SLA_TARGETS.map((target) => {
                const priorityEscalations = escalations.filter(e => e.priority === target.priority)
                const complianceCount = priorityEscalations.filter(e => {
                  const createdAt = new Date(e.created_at)
                  const now = new Date()
                  const elapsedTime = now.getTime() - createdAt.getTime()
                  return elapsedTime <= target.resolutionTimeTarget * 1000
                }).length
                const complianceRate = priorityEscalations.length > 0 
                  ? (complianceCount / priorityEscalations.length) * 100 
                  : 0

                return (
                  <div key={target.priority} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Badge className={getStatusColor(target.priority)}>
                          {target.priority.toUpperCase()}
                        </Badge>
                        <span className="font-medium">
                          {priorityEscalations.length} escalations
                        </span>
                      </div>
                      <Badge 
                        variant="outline"
                        className={complianceRate >= 85 ? 'text-green-600' : 'text-red-600'}
                      >
                        {formatPercentage(complianceRate)} compliance
                      </Badge>
                    </div>

                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Response Target</span>
                        <p className="font-medium">
                          {formatDuration(target.responseTimeTarget)}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">Resolution Target</span>
                        <p className="font-medium">
                          {formatDuration(target.resolutionTimeTarget)}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">Current Performance</span>
                        <p className="font-medium">
                          {complianceCount}/{priorityEscalations.length} on time
                        </p>
                      </div>
                    </div>

                    <Progress value={complianceRate} className="mt-3" />
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* SLA Breaches */}
      {(viewMode === 'breaches' || breaches.length > 0) && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Active SLA Breaches ({breaches.length})
              </CardTitle>
              {breaches.length > 0 && (
                <Badge variant="destructive">
                  Immediate attention required
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {breaches.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-600" />
                <p>No active SLA breaches</p>
                <p className="text-sm">All escalations are within SLA targets</p>
              </div>
            ) : (
              <div className="space-y-3">
                {breaches.map((breach) => (
                  <div
                    key={breach.escalationId}
                    className="p-4 border border-red-200 rounded-lg bg-red-50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <XCircle className="h-4 w-4 text-red-600" />
                          <h4 className="font-medium text-red-900">
                            {breach.subject}
                          </h4>
                          <Badge className={getStatusColor(breach.priority)}>
                            {breach.priority}
                          </Badge>
                        </div>
                        <div className="text-sm text-red-700">
                          <p>Overdue by: <strong>{formatDuration(breach.timeOverdue / 1000)}</strong></p>
                          <p>Breach type: {breach.breachType}</p>
                          {breach.assignedTo && (
                            <p>Assigned to: {breach.assignedTo}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline">
                          View Details
                        </Button>
                        <Button size="sm">
                          Escalate
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Performance Trends */}
      {viewMode === 'detailed' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Performance Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {performance.map((period, index) => {
                const trend = index > 0 
                  ? period.complianceRate - performance[index - 1].complianceRate
                  : 0

                return (
                  <div key={period.period} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium">{period.period}</h4>
                      <div className="flex items-center gap-2">
                        {trend > 0 ? (
                          <TrendingUp className="h-4 w-4 text-green-600" />
                        ) : trend < 0 ? (
                          <TrendingDown className="h-4 w-4 text-red-600" />
                        ) : (
                          <Activity className="h-4 w-4 text-gray-600" />
                        )}
                        <span className={`text-sm ${
                          trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-600'
                        }`}>
                          {trend > 0 ? '+' : ''}{formatPercentage(Math.abs(trend))}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Compliance</span>
                        <p className="font-medium text-lg">
                          {formatPercentage(period.complianceRate)}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">Avg Response</span>
                        <p className="font-medium">
                          {formatDuration(period.averageResponseTime)}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">Avg Resolution</span>
                        <p className="font-medium">
                          {formatDuration(period.averageResolutionTime)}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">Total</span>
                        <p className="font-medium">
                          {formatNumber(period.totalEscalations)}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">Breaches</span>
                        <p className="font-medium text-red-600">
                          {period.breaches}
                        </p>
                      </div>
                    </div>

                    <Progress value={period.complianceRate} className="mt-3" />
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 