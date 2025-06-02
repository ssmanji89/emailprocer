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
import { Progress } from '@/components/ui/progress'
import { 
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Zap,
  Users,
  Clock,
  Target,
  RefreshCw,
  Lightbulb,
  AlertCircle
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { PerformanceInsights } from '@/types/api'

export default function InsightsPage() {
  const [selectedPeriod, setSelectedPeriod] = useState('30d')

  const {
    data: insights,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['performance-insights', selectedPeriod],
    queryFn: () => apiClient.getPerformanceInsights(selectedPeriod),
    refetchInterval: 300000, // Refresh every 5 minutes
  })

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Failed to load insights</h2>
          <p className="text-gray-600 mb-4">There was an error loading the performance insights.</p>
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
          <h1 className="text-3xl font-bold tracking-tight">Performance Insights</h1>
          <p className="text-muted-foreground">
            Efficiency metrics, bottleneck identification, and optimization recommendations
          </p>
        </div>
        
        <div className="flex gap-4">
          <select 
            value={selectedPeriod} 
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="7d">7 Days</option>
            <option value="30d">30 Days</option>
            <option value="90d">90 Days</option>
          </select>
          
          <Button onClick={() => refetch()} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          {[...Array(5)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </CardHeader>
            </Card>
          ))}
        </div>
      ) : insights ? (
        <>
          {/* Efficiency Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Overall Score</CardTitle>
                <Target className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getScoreColor(insights.efficiency_metrics.overall_score)}`}>
                  {insights.efficiency_metrics.overall_score.toFixed(1)}%
                </div>
                <Progress 
                  value={insights.efficiency_metrics.overall_score} 
                  className="mt-2"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Processing Efficiency</CardTitle>
                <Zap className="h-4 w-4 text-yellow-600" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getScoreColor(insights.efficiency_metrics.processing_efficiency)}`}>
                  {insights.efficiency_metrics.processing_efficiency.toFixed(1)}%
                </div>
                <Progress 
                  value={insights.efficiency_metrics.processing_efficiency} 
                  className="mt-2"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Classification Accuracy</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getScoreColor(insights.efficiency_metrics.classification_accuracy)}`}>
                  {insights.efficiency_metrics.classification_accuracy.toFixed(1)}%
                </div>
                <Progress 
                  value={insights.efficiency_metrics.classification_accuracy} 
                  className="mt-2"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Automation Rate</CardTitle>
                <TrendingUp className="h-4 w-4 text-purple-600" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getScoreColor(insights.efficiency_metrics.automation_rate)}`}>
                  {insights.efficiency_metrics.automation_rate.toFixed(1)}%
                </div>
                <Progress 
                  value={insights.efficiency_metrics.automation_rate} 
                  className="mt-2"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Response Time Score</CardTitle>
                <Clock className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getScoreColor(insights.efficiency_metrics.response_time_score)}`}>
                  {insights.efficiency_metrics.response_time_score.toFixed(1)}%
                </div>
                <Progress 
                  value={insights.efficiency_metrics.response_time_score} 
                  className="mt-2"
                />
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Bottlenecks */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-red-600" />
                  System Bottlenecks
                </CardTitle>
                <CardDescription>
                  Critical issues impacting performance
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {insights.bottlenecks.length > 0 ? (
                  insights.bottlenecks.map((bottleneck, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="font-semibold">{bottleneck.description}</div>
                        <Badge className={getSeverityColor(bottleneck.severity)}>
                          {bottleneck.severity.toUpperCase()}
                        </Badge>
                      </div>
                      
                      <div className="text-sm text-muted-foreground mb-2">
                        Type: {bottleneck.bottleneck_type} • Impact: {bottleneck.affected_volume} emails
                      </div>
                      
                      <div className="mb-3">
                        <div className="text-sm font-medium mb-1">Impact Score</div>
                        <Progress value={bottleneck.impact_score} className="h-2" />
                        <div className="text-xs text-muted-foreground mt-1">
                          {bottleneck.impact_score.toFixed(1)}%
                        </div>
                      </div>
                      
                      {bottleneck.recommendations.length > 0 && (
                        <div>
                          <div className="text-sm font-medium mb-1">Recommendations:</div>
                          <ul className="text-sm text-muted-foreground space-y-1">
                            {bottleneck.recommendations.map((rec, i) => (
                              <li key={i} className="flex items-start gap-2">
                                <span className="text-blue-600">•</span>
                                {rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                    <p className="text-muted-foreground">No significant bottlenecks detected</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Optimization Opportunities */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-yellow-600" />
                  Optimization Opportunities
                </CardTitle>
                <CardDescription>
                  Potential improvements and their impact
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {insights.optimization_opportunities.length > 0 ? (
                  insights.optimization_opportunities
                    .sort((a, b) => b.roi_score - a.roi_score)
                    .slice(0, 5)
                    .map((opportunity, index) => (
                      <div key={opportunity.opportunity_id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="font-semibold">{opportunity.title}</div>
                          <Badge className={getEffortColor(opportunity.implementation_effort)}>
                            {opportunity.implementation_effort} effort
                          </Badge>
                        </div>
                        
                        <p className="text-sm text-muted-foreground mb-3">
                          {opportunity.description}
                        </p>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="font-medium">Time Savings</div>
                            <div className="text-muted-foreground">
                              {opportunity.potential_savings_hours}h per month
                            </div>
                          </div>
                          <div>
                            <div className="font-medium">ROI Score</div>
                            <div className={`font-semibold ${getScoreColor(opportunity.roi_score)}`}>
                              {opportunity.roi_score.toFixed(1)}%
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                ) : (
                  <div className="text-center py-8">
                    <Target className="h-12 w-12 text-blue-500 mx-auto mb-4" />
                    <p className="text-muted-foreground">System is fully optimized</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Team Insights */}
          {insights.team_insights.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-600" />
                  Team Performance Insights
                </CardTitle>
                <CardDescription>
                  Individual team performance and recommendations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {insights.team_insights.map((team, index) => (
                    <div key={team.team_id} className="border rounded-lg p-4">
                      <div className="font-semibold mb-2">{team.team_name}</div>
                      
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Efficiency</span>
                            <span className={getScoreColor(team.efficiency_score)}>
                              {team.efficiency_score.toFixed(1)}%
                            </span>
                          </div>
                          <Progress value={team.efficiency_score} className="h-2" />
                        </div>
                        
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Workload Balance</span>
                            <span className={getScoreColor(team.workload_balance)}>
                              {team.workload_balance.toFixed(1)}%
                            </span>
                          </div>
                          <Progress value={team.workload_balance} className="h-2" />
                        </div>
                        
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Skill Utilization</span>
                            <span className={getScoreColor(team.skill_utilization)}>
                              {team.skill_utilization.toFixed(1)}%
                            </span>
                          </div>
                          <Progress value={team.skill_utilization} className="h-2" />
                        </div>
                      </div>
                      
                      {team.recommendations.length > 0 && (
                        <div className="mt-3">
                          <div className="text-sm font-medium mb-1">Recommendations:</div>
                          <ul className="text-xs text-muted-foreground space-y-1">
                            {team.recommendations.slice(0, 2).map((rec, i) => (
                              <li key={i} className="flex items-start gap-1">
                                <span className="text-blue-600">•</span>
                                {rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : null}
    </div>
  )
} 