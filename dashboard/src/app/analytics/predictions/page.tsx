'use client'

import { useState } from 'react'
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
  Brain,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Users,
  Calendar,
  BarChart3,
  RefreshCw,
  Zap,
  Clock,
  Target,
  ChevronRight
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { PredictiveAnalytics } from '@/types/api'
import PredictionChart from '@/components/charts/prediction-chart'

export default function PredictionsPage() {
  const {
    data: predictions,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['predictive-analytics'],
    queryFn: () => apiClient.getPredictiveAnalytics(),
    refetchInterval: 600000, // Refresh every 10 minutes
  })

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'up': return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'down': return <TrendingDown className="h-4 w-4 text-red-600" />
      default: return <BarChart3 className="h-4 w-4 text-blue-600" />
    }
  }

  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'up': return 'text-green-600'
      case 'down': return 'text-red-600'
      default: return 'text-blue-600'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Failed to load predictions</h2>
          <p className="text-gray-600 mb-4">There was an error loading the predictive analytics.</p>
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
          <h1 className="text-3xl font-bold tracking-tight">Predictive Analytics</h1>
          <p className="text-muted-foreground">
            Volume forecasting, escalation prediction, and capacity planning insights
          </p>
        </div>
        
        <Button onClick={() => refetch()} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Predictions
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </CardHeader>
            </Card>
          ))}
        </div>
      ) : predictions ? (
        <>
          {/* Volume Predictions Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Next 7 Days</CardTitle>
                <Brain className="h-4 w-4 text-purple-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {predictions.volume_predictions.short_term.reduce((sum, item) => sum + item.predicted_volume, 0).toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground">
                  predicted emails
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
                <Target className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(predictions.volume_predictions.short_term.reduce((sum, item) => sum + item.confidence, 0) / predictions.volume_predictions.short_term.length).toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  prediction accuracy
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Capacity Gap</CardTitle>
                <Users className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {predictions.capacity_planning.capacity_gap > 0 ? '+' : ''}
                  {predictions.capacity_planning.capacity_gap}%
                </div>
                <p className="text-xs text-muted-foreground">
                  vs current capacity
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Recommended Team Size</CardTitle>
                <Users className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {predictions.capacity_planning.recommended_team_size}
                </div>
                <p className="text-xs text-muted-foreground">
                  team members needed
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Short-term Volume Predictions */}
            <Card>
              <CardHeader>
                <CardTitle>7-Day Volume Forecast</CardTitle>
                <CardDescription>
                  Predicted email volume with confidence levels
                </CardDescription>
              </CardHeader>
              <CardContent>
                {predictions.volume_predictions.short_term.length > 0 && (
                  <div className="space-y-3">
                    {predictions.volume_predictions.short_term.slice(0, 7).map((prediction, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <div className="font-medium">
                            {new Date(prediction.date).toLocaleDateString('en-US', { 
                              weekday: 'short', 
                              month: 'short', 
                              day: 'numeric' 
                            })}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {prediction.factors.slice(0, 2).join(', ')}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold">
                            {prediction.predicted_volume.toLocaleString()}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {prediction.confidence}% confidence
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Long-term Trends */}
            <Card>
              <CardHeader>
                <CardTitle>Long-term Trends</CardTitle>
                <CardDescription>
                  Monthly predictions and trend directions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {predictions.volume_predictions.long_term.slice(0, 6).map((prediction, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        {getTrendIcon(prediction.trend_direction)}
                        <div>
                          <div className="font-medium">{prediction.month}</div>
                          <div className="text-sm text-muted-foreground">
                            Seasonal: {prediction.seasonal_adjustment.toFixed(2)}x
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">
                          {prediction.predicted_volume.toLocaleString()}
                        </div>
                        <div className={`text-sm ${getTrendColor(prediction.trend_direction)}`}>
                          {prediction.trend_direction}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Escalation Predictions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                Escalation Risk Forecast
              </CardTitle>
              <CardDescription>
                Predicted escalations and risk factors
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {predictions.escalation_predictions.slice(0, 6).map((prediction, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div className="font-medium">
                        {new Date(prediction.date).toLocaleDateString()}
                      </div>
                      <Badge variant="outline">
                        {prediction.predicted_escalations} escalations
                      </Badge>
                    </div>
                    
                    <div className="space-y-2 mb-3">
                      <div className="text-sm font-medium">Risk Factors:</div>
                      {prediction.risk_factors.slice(0, 3).map((factor, i) => (
                        <div key={i} className="flex justify-between text-sm">
                          <span className="text-muted-foreground">{factor.factor}</span>
                          <span className="font-medium">{factor.impact_score}%</span>
                        </div>
                      ))}
                    </div>
                    
                    {prediction.prevention_recommendations.length > 0 && (
                      <div>
                        <div className="text-sm font-medium mb-1">Prevention:</div>
                        <div className="text-xs text-muted-foreground">
                          {prediction.prevention_recommendations[0]}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Capacity Planning */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-600" />
                  Capacity Planning
                </CardTitle>
                <CardDescription>
                  Resource requirements and recommendations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {predictions.capacity_planning.current_capacity}
                    </div>
                    <div className="text-sm text-muted-foreground">Current Capacity</div>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">
                      {predictions.capacity_planning.predicted_demand}
                    </div>
                    <div className="text-sm text-muted-foreground">Predicted Demand</div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  {predictions.capacity_planning.timeline_recommendations.map((rec, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">{rec.period}</div>
                        <div className="text-sm text-muted-foreground">{rec.action}</div>
                      </div>
                      <Badge className={getPriorityColor(rec.priority)}>
                        {rec.priority}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Pattern Evolution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-purple-600" />
                  Pattern Evolution
                </CardTitle>
                <CardDescription>
                  Emerging and declining patterns
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {predictions.pattern_evolution.map((pattern, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="font-semibold">{pattern.pattern_type}</div>
                      <div className="flex items-center gap-2">
                        {getTrendIcon(pattern.trend_direction)}
                        <Badge variant="outline">
                          {pattern.confidence}% confidence
                        </Badge>
                      </div>
                    </div>
                    
                    <p className="text-sm text-muted-foreground mb-3">
                      {pattern.impact_assessment}
                    </p>
                    
                    {pattern.adaptation_suggestions.length > 0 && (
                      <div>
                        <div className="text-sm font-medium mb-1">Adaptation Suggestions:</div>
                        <ul className="text-xs text-muted-foreground space-y-1">
                          {pattern.adaptation_suggestions.slice(0, 2).map((suggestion, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <ChevronRight className="h-3 w-3 mt-0.5 text-blue-600" />
                              {suggestion}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  )
} 