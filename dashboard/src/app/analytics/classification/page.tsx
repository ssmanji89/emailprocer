'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CategoryDistributionChart } from '@/components/charts/category-distribution-chart'
import { ConfidenceChart } from '@/components/charts/confidence-chart'
import { FeedbackForm } from '@/components/forms/feedback-form'
import { apiClient } from '@/lib/api-client'
import { formatNumber, formatPercentage } from '@/lib/utils'
import { FeedbackRequest } from '@/types/api'
import { Activity, AlertTriangle, RefreshCw, Target, ThumbsUp, Brain } from 'lucide-react'

export default function ClassificationAnalyticsPage() {
  const [showFeedbackForm, setShowFeedbackForm] = useState(false)

  const { data: classificationData, isLoading, error, refetch } = useQuery({
    queryKey: ['classification-analytics'],
    queryFn: () => apiClient.getClassificationAnalytics(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading classification analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-4" />
          <p className="text-red-500">Failed to load classification analytics</p>
          <p className="text-sm text-muted-foreground mt-2">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    )
  }

  const totalClassified = classificationData?.category_distribution.reduce((sum, cat) => sum + cat.count, 0) || 0
  const avgConfidence = classificationData?.confidence_stats.avg_confidence || 0
  const totalFeedback = classificationData?.feedback_distribution.reduce((sum, fb) => sum + fb.count, 0) || 0

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Classification Analytics</h1>
          <p className="text-muted-foreground">
            Monitor AI email classification performance and accuracy
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
            onClick={() => setShowFeedbackForm(true)}
            className="flex items-center gap-2"
          >
            <ThumbsUp className="h-4 w-4" />
            Provide Feedback
          </Button>
        </div>
      </div>

      {/* Classification Overview Stats */}
      {classificationData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Brain className="h-4 w-4" />
                Total Classified
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(totalClassified)}
              </div>
              <p className="text-xs text-muted-foreground">
                Emails processed by AI
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Target className="h-4 w-4" />
                Average Confidence
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {formatPercentage(avgConfidence / 100)}
              </div>
              <p className="text-xs text-muted-foreground">
                Classification certainty
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <ThumbsUp className="h-4 w-4" />
                Human Feedback
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {formatNumber(totalFeedback)}
              </div>
              <p className="text-xs text-muted-foreground">
                Feedback submissions
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Categories Found</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">
                {classificationData.category_distribution.length}
              </div>
              <p className="text-xs text-muted-foreground">
                Distinct email types
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Charts Section */}
      {classificationData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CategoryDistributionChart data={classificationData.category_distribution} />
          <ConfidenceChart 
            stats={classificationData.confidence_stats}
            categories={classificationData.category_distribution}
          />
        </div>
      )}

      {/* Feedback Analysis */}
      {classificationData && classificationData.feedback_distribution.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ThumbsUp className="h-5 w-5" />
              Human Feedback Analysis
            </CardTitle>
            <CardDescription>
              Feedback from users on classification accuracy
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {classificationData.feedback_distribution.map((feedback) => (
                <div key={feedback.feedback} className="text-center">
                  <div className="text-2xl font-bold">
                    {formatNumber(feedback.count)}
                  </div>
                  <div className="text-sm text-muted-foreground capitalize">
                    {feedback.feedback.replace('_', ' ')}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {formatPercentage(feedback.count / totalFeedback)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Model Performance Insights */}
      {classificationData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Model Performance Insights
            </CardTitle>
            <CardDescription>
              AI classification model analysis and recommendations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">Confidence Distribution</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>High Confidence (&gt;80%)</span>
                    <span className="font-semibold text-green-600">
                      {classificationData.category_distribution.filter(cat => cat.avg_confidence > 80).length} categories
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Medium Confidence (60-80%)</span>
                    <span className="font-semibold text-yellow-600">
                      {classificationData.category_distribution.filter(cat => cat.avg_confidence >= 60 && cat.avg_confidence <= 80).length} categories
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Low Confidence (&lt;60%)</span>
                    <span className="font-semibold text-red-600">
                      {classificationData.category_distribution.filter(cat => cat.avg_confidence < 60).length} categories
                    </span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">Performance Metrics</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Average Confidence</span>
                    <span className="font-semibold">
                      {formatPercentage(avgConfidence / 100)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Confidence Range</span>
                    <span className="font-semibold">
                      {formatPercentage(classificationData.confidence_stats.min_confidence / 100)} - {formatPercentage(classificationData.confidence_stats.max_confidence / 100)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Categories with High Volume</span>
                    <span className="font-semibold">
                      {classificationData.category_distribution.filter(cat => cat.count > totalClassified / classificationData.category_distribution.length).length}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Feedback Form Modal */}
      {showFeedbackForm && (
        <FeedbackForm 
          onClose={() => setShowFeedbackForm(false)}
          onSubmit={async (feedback: FeedbackRequest) => {
            try {
              await apiClient.submitFeedback(feedback)
              setShowFeedbackForm(false)
              refetch() // Refresh data after feedback submission
            } catch (error) {
              console.error('Failed to submit feedback:', error)
            }
          }}
        />
      )}
    </div>
  )
} 