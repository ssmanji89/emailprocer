'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ProcessingChart } from '@/components/charts/processing-chart'
import { apiClient } from '@/lib/api-client'
import { formatNumber, formatPercentage, formatDuration } from '@/lib/utils'
import { Activity, AlertTriangle, RefreshCw } from 'lucide-react'

export default function ProcessingAnalyticsPage() {
  const [timeRange, setTimeRange] = useState(7)

  const { data: processingData, isLoading, error, refetch } = useQuery({
    queryKey: ['processing-analytics', timeRange],
    queryFn: () => apiClient.getProcessingAnalytics(timeRange),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: processingStatus } = useQuery({
    queryKey: ['processing-status'],
    queryFn: () => apiClient.getProcessingStatus(),
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  const handleTriggerProcessing = async () => {
    try {
      await apiClient.triggerProcessing()
      // Refetch data after triggering
      setTimeout(() => refetch(), 1000)
    } catch (error) {
      console.error('Failed to trigger processing:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading processing analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-4" />
          <p className="text-red-500">Failed to load processing analytics</p>
          <p className="text-sm text-muted-foreground mt-2">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Processing Analytics</h1>
          <p className="text-muted-foreground">
            Monitor email processing performance and trends
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
          <Button
            onClick={handleTriggerProcessing}
            className="flex items-center gap-2"
          >
            <Activity className="h-4 w-4" />
            Trigger Processing
          </Button>
        </div>
      </div>

      {/* Time Range Selector */}
      <div className="flex gap-2">
        {[1, 7, 14, 30, 90].map((days) => (
          <Button
            key={days}
            variant={timeRange === days ? "default" : "outline"}
            size="sm"
            onClick={() => setTimeRange(days)}
          >
            {days === 1 ? '24h' : `${days}d`}
          </Button>
        ))}
      </div>

      {/* Current Processing Status */}
      {processingStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Current Processing Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">Status</div>
                <div className="text-lg font-semibold capitalize">
                  {processingStatus.status}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Active Jobs</div>
                <div className="text-lg font-semibold">
                  {processingStatus.active_jobs}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Last Run</div>
                <div className="text-lg font-semibold">
                  {new Date(processingStatus.last_run).toLocaleTimeString()}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Next Run</div>
                <div className="text-lg font-semibold">
                  {new Date(processingStatus.next_run).toLocaleTimeString()}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Processing Overview Stats */}
      {processingData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Processed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(processingData.overall.total_processed)}
              </div>
              <p className="text-xs text-muted-foreground">
                Over {processingData.period_days} days
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {formatPercentage(
                  processingData.overall.successful / processingData.overall.total_processed
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                {formatNumber(processingData.overall.successful)} successful
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Average Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatDuration(processingData.overall.avg_processing_time_ms / 1000)}
              </div>
              <p className="text-xs text-muted-foreground">
                Per email processed
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Responses Sent</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {formatNumber(processingData.overall.responses_sent)}
              </div>
              <p className="text-xs text-muted-foreground">
                Automated responses
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Escalations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {formatNumber(processingData.overall.escalations_created)}
              </div>
              <p className="text-xs text-muted-foreground">
                Required human review
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Processing Trends Chart */}
      {processingData && (
        <ProcessingChart data={processingData} />
      )}
    </div>
  )
} 