'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { ProcessingAnalytics } from '@/types/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatNumber } from '@/lib/utils'

interface ProcessingChartProps {
  data: ProcessingAnalytics
}

export function ProcessingChart({ data }: ProcessingChartProps) {
  const chartData = data.daily_trends.map(trend => ({
    date: new Date(trend.date).toLocaleDateString(),
    count: trend.count,
    avgTime: trend.avg_time_ms / 1000, // Convert to seconds
  }))

  return (
    <Card className="col-span-4">
      <CardHeader>
        <CardTitle>Email Processing Trends</CardTitle>
        <CardDescription>
          Daily email processing volume and average processing time over the last {data.period_days} days
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {formatNumber(data.overall.successful)}
            </div>
            <div className="text-sm text-muted-foreground">Successful</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {formatNumber(data.overall.failed)}
            </div>
            <div className="text-sm text-muted-foreground">Failed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {formatNumber(data.overall.responses_sent)}
            </div>
            <div className="text-sm text-muted-foreground">Responses Sent</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {formatNumber(data.overall.escalations_created)}
            </div>
            <div className="text-sm text-muted-foreground">Escalations</div>
          </div>
        </div>
        
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip 
              formatter={(value: any, name: string) => [
                name === 'count' ? formatNumber(value) : `${value.toFixed(2)}s`,
                name === 'count' ? 'Emails Processed' : 'Avg Processing Time'
              ]}
            />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="count" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={{ r: 4 }}
            />
            <Line 
              yAxisId="right"
              type="monotone" 
              dataKey="avgTime" 
              stroke="#f59e0b" 
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
} 