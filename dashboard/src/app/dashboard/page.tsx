'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api-client'
import { formatNumber, formatPercentage, formatRelativeTime } from '@/lib/utils'
import { Activity, Mail, AlertTriangle, TrendingUp, Clock, CheckCircle } from 'lucide-react'

export default function DashboardPage() {
  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => apiClient.getDashboardData(),
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealthCheck(),
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-4" />
          <p className="text-red-500">Failed to load dashboard data</p>
          <p className="text-sm text-muted-foreground mt-2">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of EmailBot processing and analytics
        </p>
      </div>

      {/* System Health Status */}
      {healthData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className={`h-5 w-5 ${
                healthData.status === 'healthy' ? 'text-green-500' : 
                healthData.status === 'degraded' ? 'text-yellow-500' : 'text-red-500'
              }`} />
              System Status: {healthData.status.toUpperCase()}
            </CardTitle>
            <CardDescription>
              Last updated: {formatRelativeTime(healthData.timestamp)}
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {/* Key Metrics Grid */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Emails Processed Today
              </CardTitle>
              <Mail className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(dashboardData.processing.emails_processed_today)}
              </div>
              <p className="text-xs text-muted-foreground">
                Total: {formatNumber(dashboardData.processing.emails_processed_total)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Success Rate
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatPercentage(dashboardData.processing.processing_success_rate)}
              </div>
              <p className="text-xs text-muted-foreground">
                Classification confidence: {formatPercentage(dashboardData.classification.avg_confidence_score)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Active Jobs
              </CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {dashboardData.processing.active_processing_jobs}
              </div>
              <p className="text-xs text-muted-foreground">
                Avg time: {dashboardData.processing.avg_processing_time_seconds.toFixed(1)}s
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Active Escalations
              </CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {dashboardData.active_escalations}
              </div>
              <p className="text-xs text-muted-foreground">
                Automation opportunities: {dashboardData.automation_opportunities}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Additional Metrics */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Processing Metrics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Uptime</span>
                <span className="text-sm font-medium">
                  {dashboardData.metrics.uptime_hours.toFixed(1)}h
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Emails/Hour</span>
                <span className="text-sm font-medium">
                  {dashboardData.metrics.emails_per_hour.toFixed(1)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Last Run</span>
                <span className="text-sm font-medium">
                  {formatRelativeTime(dashboardData.processing.last_processing_run)}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Classification Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Total Classified</span>
                <span className="text-sm font-medium">
                  {formatNumber(dashboardData.classification.total_classified)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">High Confidence</span>
                <span className="text-sm font-medium">
                  {formatPercentage(dashboardData.classification.high_confidence_rate)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Categories</span>
                <span className="text-sm font-medium">
                  {dashboardData.classification.categories_identified}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Performance Indicators</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Escalation Rate</span>
                <span className="text-sm font-medium">
                  {formatPercentage(dashboardData.metrics.escalation_rate)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Automation Rate</span>
                <span className="text-sm font-medium">
                  {formatPercentage(dashboardData.metrics.automation_rate)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Satisfaction Score</span>
                <span className="text-sm font-medium">
                  {dashboardData.metrics.user_satisfaction_score.toFixed(1)}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
} 