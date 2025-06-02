'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatNumber, formatPercentage } from '@/lib/utils'

interface ConfidenceStats {
  avg_confidence: number;
  min_confidence: number;
  max_confidence: number;
}

interface CategoryData {
  category: string;
  count: number;
  avg_confidence: number;
}

interface ConfidenceChartProps {
  stats: ConfidenceStats;
  categories: CategoryData[];
}

export function ConfidenceChart({ stats, categories }: ConfidenceChartProps) {
  // Create confidence distribution histogram
  const createHistogramData = () => {
    const bins = [
      { range: '0-20%', min: 0, max: 20, count: 0 },
      { range: '20-40%', min: 20, max: 40, count: 0 },
      { range: '40-60%', min: 40, max: 60, count: 0 },
      { range: '60-80%', min: 60, max: 80, count: 0 },
      { range: '80-100%', min: 80, max: 100, count: 0 },
    ]

    // Distribute categories into bins based on their confidence
    categories.forEach(cat => {
      const binIndex = Math.min(Math.floor(cat.avg_confidence / 20), 4)
      if (binIndex >= 0 && binIndex < bins.length) {
        bins[binIndex].count += cat.count
      }
    })

    return bins
  }

  // Create scatter plot data for category confidence vs count
  const scatterData = categories.map(cat => ({
    name: cat.category,
    confidence: cat.avg_confidence,
    count: cat.count,
    // Color coding based on confidence level
    color: cat.avg_confidence >= 80 ? '#10b981' : // Green for high confidence
           cat.avg_confidence >= 60 ? '#f59e0b' : // Orange for medium confidence  
           '#ef4444' // Red for low confidence
  }))

  const histogramData = createHistogramData()

  const getConfidenceLevel = (confidence: number) => {
    if (confidence >= 80) return { level: 'High', color: 'text-green-600' }
    if (confidence >= 60) return { level: 'Medium', color: 'text-yellow-600' }
    return { level: 'Low', color: 'text-red-600' }
  }

  const confidenceLevel = getConfidenceLevel(stats.avg_confidence)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Confidence Analysis</CardTitle>
        <CardDescription>
          Classification confidence score distribution and analysis
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Confidence Stats Overview */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-sm text-muted-foreground">Average</div>
            <div className={`text-lg font-bold ${confidenceLevel.color}`}>
              {formatPercentage(stats.avg_confidence / 100)}
            </div>
            <div className="text-xs text-muted-foreground">
              {confidenceLevel.level} Confidence
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Minimum</div>
            <div className="text-lg font-bold">
              {formatPercentage(stats.min_confidence / 100)}
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Maximum</div>
            <div className="text-lg font-bold">
              {formatPercentage(stats.max_confidence / 100)}
            </div>
          </div>
        </div>

        {/* Confidence Distribution Histogram */}
        <div>
          <h4 className="font-semibold mb-4">Confidence Distribution</h4>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={histogramData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip 
                  formatter={(value: any) => [formatNumber(value), 'Emails']}
                  labelFormatter={(label) => `Confidence: ${label}`}
                />
                <Bar 
                  dataKey="count" 
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Confidence Scatter Plot */}
        <div>
          <h4 className="font-semibold mb-4">Category Confidence vs Volume</h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart data={scatterData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="confidence" 
                  type="number"
                  domain={[0, 100]}
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `${value}%`}
                />
                <YAxis 
                  dataKey="count" 
                  type="number"
                  tick={{ fontSize: 12 }}
                />
                <Tooltip 
                  formatter={(value: any, name: string) => [
                    name === 'count' ? formatNumber(value) : formatPercentage(value / 100),
                    name === 'count' ? 'Emails' : 'Confidence'
                  ]}
                  labelFormatter={(label, payload) => {
                    if (payload && payload[0]) {
                      return `Category: ${payload[0].payload.name}`
                    }
                    return label
                  }}
                />
                <Scatter dataKey="count" fill="#8b5cf6" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Confidence Threshold Analysis */}
        <div>
          <h4 className="font-semibold mb-4">Confidence Threshold Analysis</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {categories.filter(cat => cat.avg_confidence >= 80).length}
                </div>
                <div className="text-sm text-muted-foreground">High Confidence</div>
                <div className="text-xs text-muted-foreground">≥80% categories</div>
              </div>
            </div>
            <div className="p-4 border rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {categories.filter(cat => cat.avg_confidence >= 60 && cat.avg_confidence < 80).length}
                </div>
                <div className="text-sm text-muted-foreground">Medium Confidence</div>
                <div className="text-xs text-muted-foreground">60-79% categories</div>
              </div>
            </div>
            <div className="p-4 border rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {categories.filter(cat => cat.avg_confidence < 60).length}
                </div>
                <div className="text-sm text-muted-foreground">Low Confidence</div>
                <div className="text-xs text-muted-foreground">&lt;60% categories</div>
              </div>
            </div>
          </div>
        </div>

        {/* Low Confidence Categories Alert */}
        {categories.filter(cat => cat.avg_confidence < 60).length > 0 && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <h5 className="font-semibold text-red-800 mb-2">Low Confidence Categories</h5>
            <div className="space-y-1">
              {categories
                .filter(cat => cat.avg_confidence < 60)
                .sort((a, b) => a.avg_confidence - b.avg_confidence)
                .slice(0, 5)
                .map(cat => (
                  <div key={cat.category} className="flex justify-between text-sm">
                    <span className="text-red-700">{cat.category}</span>
                    <span className="text-red-600 font-medium">
                      {formatPercentage(cat.avg_confidence / 100)}
                    </span>
                  </div>
                ))}
            </div>
            <p className="text-xs text-red-600 mt-2">
              These categories may benefit from additional training data or review.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 