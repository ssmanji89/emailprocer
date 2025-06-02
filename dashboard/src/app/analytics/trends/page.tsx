'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Calendar,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Clock,
  Zap,
  AlertTriangle,
  RefreshCw
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { TrendParams, TrendAnalytics } from '@/types/api'
import TrendAnalysisChart from '@/components/charts/trend-analysis-chart'
import PredictionChart from '@/components/charts/prediction-chart'

export default function TrendsPage() {
  const [trendParams, setTrendParams] = useState<TrendParams>({
    period: '30d',
    granularity: 'day',
    include_forecast: true,
    include_seasonality: true
  })

  const {
    data: trendData,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['trend-analytics', trendParams],
    queryFn: () => apiClient.getTrendAnalytics(trendParams),
    refetchInterval: 60000, // Refresh every minute
  })

  const handlePeriodChange = (period: string) => {
    setTrendParams(prev => ({ ...prev, period: period as TrendParams['period'] }))
  }

  const handleGranularityChange = (granularity: string) => {
    setTrendParams(prev => ({ ...prev, granularity: granularity as TrendParams['granularity'] }))
  }

  const getOverallTrend = () => {
    if (!trendData?.volume_trends?.length) return null
    
    const recent = trendData.volume_trends.slice(-7)
    const older = trendData.volume_trends.slice(-14, -7)
    
    if (recent.length < 2 || older.length < 2) return null
    
    const recentAvg = recent.reduce((sum, item) => sum + item.emails_received, 0) / recent.length
    const olderAvg = older.reduce((sum, item) => sum + item.emails_received, 0) / older.length
    
    const changePercent = ((recentAvg - olderAvg) / olderAvg) * 100
    
    return {
      direction: changePercent > 5 ? 'up' : changePercent < -5 ? 'down' : 'stable',
      percent: Math.abs(changePercent)
    }
  }

  const getPeakHours = () => {
    if (!trendData?.seasonal_patterns?.length) return []
    
    return trendData.seasonal_patterns
      .filter(pattern => pattern.peak_indicator)
      .sort((a, b) => b.avg_volume - a.avg_volume)
      .slice(0, 3)
  }

  const trend = getOverallTrend()
  const peakHours = getPeakHours()

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Failed to load trend data</h2>
          <p className="text-gray-600 mb-4">There was an error loading the analytics data.</p>
          <Button onClick={() => refetch()} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Trend Analysis</h1>
          <p className="text-muted-foreground">
            Historical patterns, seasonal analysis, and predictive insights
          </p>
        </div>
        
        <div className="flex gap-4">
          <select 
            value={trendParams.period} 
            onChange={(e) => handlePeriodChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="7d">7 Days</option>
            <option value="30d">30 Days</option>
            <option value="90d">90 Days</option>
            <option value="6m">6 Months</option>
            <option value="1y">1 Year</option>
          </select>
          
          <select 
            value={trendParams.granularity} 
            onChange={(e) => handleGranularityChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="hour">Hourly</option>
            <option value="day">Daily</option>
            <option value="week">Weekly</option>
            <option value="month">Monthly</option>
          </select>
          
          <Button onClick={() => refetch()} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </CardHeader>
            </Card>
          ))}
        </div>
      ) : (
        <>
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Overall Trend */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Overall Trend</CardTitle>
                {trend?.direction === 'up' ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : trend?.direction === 'down' ? (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                ) : (
                  <BarChart3 className="h-4 w-4 text-blue-600" />
                )}
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {trend?.direction === 'up' ? '+' : trend?.direction === 'down' ? '-' : ''}
                  {trend?.percent?.toFixed(1) || '0.0'}%
                </div>
                <p className="text-xs text-muted-foreground">
                  vs previous period
                </p>
              </CardContent>
            </Card>

            {/* Total Volume */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Volume</CardTitle>
                <BarChart3 className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {trendData?.volume_trends?.reduce((sum, item) => sum + item.emails_received, 0)?.toLocaleString() || '0'}
                </div>
                <p className="text-xs text-muted-foreground">
                  emails in selected period
                </p>
              </CardContent>
            </Card>

            {/* Processing Rate */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Processing Rate</CardTitle>
                <Zap className="h-4 w-4 text-yellow-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {trendData?.volume_trends?.length ? 
                    (trendData.volume_trends.reduce((sum, item) => sum + item.processing_rate, 0) / trendData.volume_trends.length).toFixed(1) : '0.0'
                  }%
                </div>
                <p className="text-xs text-muted-foreground">
                  processing success rate
                </p>
              </CardContent>
            </Card>

            {/* Peak Hours */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Peak Hours</CardTitle>
                <Clock className="h-4 w-4 text-purple-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {peakHours.length > 0 ? `${peakHours[0].hour_of_day}:00` : 'N/A'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {peakHours.length > 1 && `+${peakHours.length - 1} more`}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Main Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Volume Trends Chart */}
            <Card className="col-span-1">
              <CardHeader>
                <CardTitle>Volume Trends</CardTitle>
                <CardDescription>
                  Email volume and processing patterns over time
                </CardDescription>
              </CardHeader>
              <CardContent>
                {trendData?.volume_trends && (
                  <TrendAnalysisChart 
                    data={trendData.volume_trends}
                    type="volume"
                    height={300}
                  />
                )}
              </CardContent>
            </Card>

            {/* Performance Trends Chart */}
            <Card className="col-span-1">
              <CardHeader>
                <CardTitle>Performance Trends</CardTitle>
                <CardDescription>
                  Success rates and confidence metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                {trendData?.performance_trends && (
                  <TrendAnalysisChart 
                    data={trendData.performance_trends}
                    type="performance"
                    height={300}
                  />
                )}
              </CardContent>
            </Card>
          </div>

          {/* Forecasting Section */}
          {trendData?.forecasting && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* 7-day Forecast Chart */}
              <Card className="col-span-2">
                <CardHeader>
                  <CardTitle>7-Day Forecast</CardTitle>
                  <CardDescription>
                    Predicted email volume with confidence intervals
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <PredictionChart 
                    data={trendData.forecasting.next_7_days}
                    height={300}
                  />
                </CardContent>
              </Card>

              {/* 30-day Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>30-Day Outlook</CardTitle>
                  <CardDescription>
                    Long-term volume predictions
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="text-sm font-medium text-muted-foreground">Predicted Total</div>
                    <div className="text-2xl font-bold">
                      {trendData.forecasting.next_30_days_summary.predicted_total.toLocaleString()}
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-sm font-medium text-muted-foreground">Growth Rate</div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-semibold">
                        {trendData.forecasting.next_30_days_summary.growth_rate > 0 ? '+' : ''}
                        {trendData.forecasting.next_30_days_summary.growth_rate.toFixed(1)}%
                      </span>
                      <Badge variant={trendData.forecasting.next_30_days_summary.growth_rate > 0 ? 'default' : 'secondary'}>
                        {trendData.forecasting.next_30_days_summary.growth_rate > 0 ? 'Growth' : 'Decline'}
                      </Badge>
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-sm font-medium text-muted-foreground">Seasonal Factor</div>
                    <div className="text-lg font-semibold">
                      {trendData.forecasting.next_30_days_summary.seasonal_factor.toFixed(2)}x
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Category Trends */}
          {trendData?.category_trends && trendData.category_trends.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Category Trends</CardTitle>
                <CardDescription>
                  Growth patterns by email category
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {trendData.category_trends.slice(0, 6).map((category) => (
                    <div key={category.category} className="p-4 border rounded-lg">
                      <div className="font-semibold">{category.category}</div>
                      <div className="text-sm text-muted-foreground">
                        {category.trend_data.reduce((sum, item) => sum + item.count, 0)} emails
                      </div>
                      {category.trend_data.length > 0 && (
                        <div className="mt-2">
                          <Badge variant={
                            category.trend_data[category.trend_data.length - 1].growth_rate > 0 ? 'default' : 'secondary'
                          }>
                            {category.trend_data[category.trend_data.length - 1].growth_rate > 0 ? '+' : ''}
                            {category.trend_data[category.trend_data.length - 1].growth_rate.toFixed(1)}%
                          </Badge>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Seasonal Patterns */}
          {trendData?.seasonal_patterns && trendData.seasonal_patterns.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Seasonal Patterns</CardTitle>
                <CardDescription>
                  Email volume patterns throughout the day
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-6 md:grid-cols-12 gap-2">
                  {trendData.seasonal_patterns.map((pattern) => (
                    <div 
                      key={pattern.hour_of_day}
                      className={`text-center p-2 rounded ${
                        pattern.peak_indicator 
                          ? 'bg-blue-100 border-2 border-blue-500' 
                          : 'bg-gray-50 border border-gray-200'
                      }`}
                    >
                      <div className="text-xs font-medium">
                        {pattern.hour_of_day.toString().padStart(2, '0')}:00
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {Math.round(pattern.avg_volume)}
                      </div>
                      {pattern.peak_indicator && (
                        <div className="text-xs text-blue-600 font-medium">Peak</div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
} 