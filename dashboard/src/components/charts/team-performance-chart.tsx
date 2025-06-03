'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { apiClient } from '@/lib/api-client'
import { TeamPerformance } from '@/types/api'
import { formatNumber, formatDuration, formatPercentage, getStatusColor } from '@/lib/utils'
import {
  Users,
  Clock,
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  Loader2,
  BarChart3,
  PieChart,
  RefreshCw,
  Download,
  Filter,
  Eye
} from 'lucide-react'

interface TeamPerformanceChartProps {
  teamId?: string
  period?: string
  showActions?: boolean
}

export function TeamPerformanceChart({ 
  teamId = 'all', 
  period = '7d',
  showActions = true 
}: TeamPerformanceChartProps) {
  const [performanceData, setPerformanceData] = useState<TeamPerformance[]>([])
  const [workloadData, setWorkloadData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedPeriod, setSelectedPeriod] = useState(period)
  const [selectedTeam, setSelectedTeam] = useState(teamId)
  const [viewMode, setViewMode] = useState<'overview' | 'detailed'>('overview')

  useEffect(() => {
    loadPerformanceData()
  }, [selectedTeam, selectedPeriod])

  const loadPerformanceData = async () => {
    setIsLoading(true)
    try {
      const [performance, workload] = await Promise.all([
        apiClient.getTeamPerformance(selectedTeam, selectedPeriod),
        apiClient.getTeamWorkload(selectedTeam === 'all' ? undefined : selectedTeam)
      ])
      
      setPerformanceData(performance)
      setWorkloadData(workload)
    } catch (error) {
      console.error('Failed to load team performance data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const calculateOverallMetrics = () => {
    if (performanceData.length === 0) {
      return {
        totalEscalations: 0,
        avgResponseTime: 0,
        resolutionRate: 0,
        slaCompliance: 0
      }
    }

    const totalEscalations = performanceData.reduce((sum, team) => sum + team.total_escalations, 0)
    const avgResponseTime = performanceData.reduce((sum, team) => sum + team.avg_response_time, 0) / performanceData.length
    const totalResolved = performanceData.reduce((sum, team) => sum + team.resolved_escalations, 0)
    const resolutionRate = totalEscalations > 0 ? (totalResolved / totalEscalations) * 100 : 0
    const avgSlaCompliance = performanceData.reduce((sum, team) => sum + team.sla_compliance_rate, 0) / performanceData.length

    return {
      totalEscalations,
      avgResponseTime,
      resolutionRate,
      slaCompliance: avgSlaCompliance
    }
  }

  const getPerformanceColor = (value: number, type: 'response_time' | 'sla_compliance' | 'resolution_rate') => {
    switch (type) {
      case 'response_time':
        if (value <= 1800) return 'text-green-600' // <= 30 minutes
        if (value <= 3600) return 'text-yellow-600' // <= 1 hour
        return 'text-red-600'
      case 'sla_compliance':
        if (value >= 95) return 'text-green-600'
        if (value >= 85) return 'text-yellow-600'
        return 'text-red-600'
      case 'resolution_rate':
        if (value >= 80) return 'text-green-600'
        if (value >= 60) return 'text-yellow-600'
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getWorkloadStatusColor = (utilization: number) => {
    if (utilization >= 90) return 'bg-red-100 text-red-800'
    if (utilization >= 75) return 'bg-yellow-100 text-yellow-800'
    if (utilization >= 50) return 'bg-blue-100 text-blue-800'
    return 'bg-green-100 text-green-800'
  }

  const getWorkloadStatus = (utilization: number) => {
    if (utilization >= 90) return 'Overloaded'
    if (utilization >= 75) return 'High Load'
    if (utilization >= 50) return 'Normal Load'
    return 'Low Load'
  }

  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous) {
      return <TrendingUp className="h-4 w-4 text-green-600" />
    } else if (current < previous) {
      return <TrendingDown className="h-4 w-4 text-red-600" />
    }
    return <Activity className="h-4 w-4 text-gray-600" />
  }

  const exportData = () => {
    const csvData = performanceData.map(team => ({
      'Team': team.team_name,
      'Total Escalations': team.total_escalations,
      'Resolved': team.resolved_escalations,
      'Pending': team.pending_escalations,
      'Resolution Rate (%)': ((team.resolved_escalations / team.total_escalations) * 100).toFixed(1),
      'Avg Response Time (min)': (team.avg_response_time / 60).toFixed(1),
      'SLA Compliance (%)': team.sla_compliance_rate.toFixed(1)
    }))

    const csv = [
      Object.keys(csvData[0]).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `team-performance-${selectedPeriod}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const overallMetrics = calculateOverallMetrics()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Team Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin mr-2" />
            <span>Loading performance data...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Team Performance Dashboard
            </CardTitle>
            {showActions && (
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
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadPerformanceData}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-3 w-3" />
                  Refresh
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={exportData}
                  className="flex items-center gap-2"
                >
                  <Download className="h-3 w-3" />
                  Export
                </Button>
              </div>
            )}
          </div>
        </CardHeader>

        {/* Overall Metrics */}
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">Total Escalations</span>
              </div>
              <p className="text-2xl font-bold text-blue-900 mt-1">
                {formatNumber(overallMetrics.totalEscalations)}
              </p>
            </div>

            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-green-900">Avg Response</span>
              </div>
              <p className="text-2xl font-bold text-green-900 mt-1">
                {formatDuration(overallMetrics.avgResponseTime)}
              </p>
            </div>

            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-900">Resolution Rate</span>
              </div>
              <p className="text-2xl font-bold text-purple-900 mt-1">
                {formatPercentage(overallMetrics.resolutionRate)}
              </p>
            </div>

            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-orange-600" />
                <span className="text-sm font-medium text-orange-900">SLA Compliance</span>
              </div>
              <p className="text-2xl font-bold text-orange-900 mt-1">
                {formatPercentage(overallMetrics.slaCompliance)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Team Performance Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Team Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {performanceData.map((team) => {
                const resolutionRate = team.total_escalations > 0 
                  ? (team.resolved_escalations / team.total_escalations) * 100 
                  : 0

                return (
                  <div key={team.team_id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium">{team.team_name}</h4>
                      <Badge variant="outline">
                        {team.total_escalations} escalations
                      </Badge>
                    </div>

                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Response Time</span>
                        <p className={`font-medium ${getPerformanceColor(team.avg_response_time, 'response_time')}`}>
                          {formatDuration(team.avg_response_time)}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">Resolution Rate</span>
                        <p className={`font-medium ${getPerformanceColor(resolutionRate, 'resolution_rate')}`}>
                          {formatPercentage(resolutionRate)}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">SLA Compliance</span>
                        <p className={`font-medium ${getPerformanceColor(team.sla_compliance_rate, 'sla_compliance')}`}>
                          {formatPercentage(team.sla_compliance_rate)}
                        </p>
                      </div>
                    </div>

                    {/* Progress bars for visual representation */}
                    <div className="mt-3 space-y-2">
                      <div>
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>Resolved</span>
                          <span>{team.resolved_escalations}/{team.total_escalations}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${resolutionRate}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Team Workload Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Current Workload</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {workloadData.map((team) => (
                <div key={team.team_id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium">{team.team_name}</h4>
                    <Badge className={getWorkloadStatusColor(team.capacity_utilization)}>
                      {getWorkloadStatus(team.capacity_utilization)}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Active Escalations</span>
                      <p className="font-medium text-lg">{team.active_escalations}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Capacity Utilization</span>
                      <p className="font-medium text-lg">
                        {formatPercentage(team.capacity_utilization)}
                      </p>
                    </div>
                  </div>

                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>Capacity</span>
                      <span>{formatPercentage(team.capacity_utilization)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          team.capacity_utilization >= 90 
                            ? 'bg-red-500' 
                            : team.capacity_utilization >= 75 
                            ? 'bg-yellow-500' 
                            : 'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(100, team.capacity_utilization)}%` }}
                      />
                    </div>
                  </div>

                  <div className="mt-3 text-xs text-gray-600">
                    Avg Response: {formatDuration(team.avg_response_time)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 