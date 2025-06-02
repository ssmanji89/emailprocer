'use client'

import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import { apiClient } from '@/lib/api-client'
import { ROICalculatorChart } from '@/components/charts/roi-calculator-chart'

export default function ROICalculatorPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['patterns-roi'],
    queryFn: () => apiClient.getPatternAnalytics(),
    refetchInterval: 30000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-2 text-sm text-muted-foreground">Loading ROI data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-red-600">
            <p>Error loading ROI data: {error.message}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/patterns">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Patterns
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">ROI Calculator</h1>
            <p className="text-muted-foreground">
              Calculate return on investment for automation patterns
            </p>
          </div>
        </div>
      </div>

      {/* ROI Calculator */}
      <ROICalculatorChart patterns={data?.automation_candidates || []} />
    </div>
  )
} 