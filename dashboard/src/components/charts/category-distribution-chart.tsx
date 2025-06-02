'use client'

import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatNumber, formatPercentage } from '@/lib/utils'

interface CategoryData {
  category: string;
  count: number;
  avg_confidence: number;
}

interface CategoryDistributionChartProps {
  data: CategoryData[]
}

const COLORS = [
  '#3b82f6', // Blue
  '#10b981', // Green  
  '#f59e0b', // Orange
  '#ef4444', // Red
  '#8b5cf6', // Purple
  '#06b6d4', // Cyan
  '#84cc16', // Lime
  '#f97316', // Orange-red
  '#ec4899', // Pink
  '#6366f1', // Indigo
]

export function CategoryDistributionChart({ data }: CategoryDistributionChartProps) {
  const totalEmails = data.reduce((sum, cat) => sum + cat.count, 0)
  
  const chartData = data.map((item, index) => ({
    ...item,
    percentage: (item.count / totalEmails) * 100,
    color: COLORS[index % COLORS.length]
  }))

  const topCategories = chartData
    .sort((a, b) => b.count - a.count)
    .slice(0, 8) // Show top 8 categories

  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Distribution</CardTitle>
        <CardDescription>
          Email classification breakdown by category
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Pie Chart */}
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={topCategories}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="count"
                >
                  {topCategories.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: any, name: string) => [
                    formatNumber(value),
                    'Emails'
                  ]}
                  labelFormatter={(label) => `${label}`}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Legend with stats */}
          <div className="grid grid-cols-1 gap-2">
            {topCategories.map((category, index) => (
              <div key={category.category} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: category.color }}
                  />
                  <span className="font-medium">{category.category}</span>
                </div>
                <div className="flex items-center gap-4 text-muted-foreground">
                  <span>{formatNumber(category.count)}</span>
                  <span>{formatPercentage(category.percentage / 100)}</span>
                  <span className="text-xs">
                    {formatPercentage(category.avg_confidence / 100)} confidence
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Bar Chart for detailed view */}
          <div className="mt-6">
            <h4 className="font-semibold mb-4">Category Volume & Confidence</h4>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topCategories} margin={{ bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="category" 
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip 
                    formatter={(value: any, name: string) => [
                      name === 'count' ? formatNumber(value) : formatPercentage(value / 100),
                      name === 'count' ? 'Emails' : 'Avg Confidence'
                    ]}
                  />
                  <Bar 
                    yAxisId="left"
                    dataKey="count" 
                    fill="#3b82f6" 
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar 
                    yAxisId="right"
                    dataKey="avg_confidence" 
                    fill="#10b981" 
                    radius={[4, 4, 0, 0]}
                    opacity={0.7}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 