'use client'

import { useMemo } from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'

interface PredictionChartProps {
  data: Array<{
    date: string
    predicted_volume: number
    confidence_interval: {
      lower: number
      upper: number
    }
  }>
  height?: number
}

export default function PredictionChart({ 
  data, 
  height = 300 
}: PredictionChartProps) {
  const chartData = useMemo(() => {
    return data.map(item => ({
      date: new Date(item.date).toLocaleDateString(),
      'Predicted Volume': item.predicted_volume,
      'Lower Bound': item.confidence_interval.lower,
      'Upper Bound': item.confidence_interval.upper,
      'Confidence Range': item.confidence_interval.upper - item.confidence_interval.lower
    }))
  }, [data])

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id="confidence" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ddd6fe" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#ddd6fe" stopOpacity={0.2}/>
          </linearGradient>
          <linearGradient id="prediction" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
        <XAxis 
          dataKey="date" 
          tick={{ fontSize: 12 }}
          stroke="#6b7280"
        />
        <YAxis 
          tick={{ fontSize: 12 }}
          stroke="#6b7280"
        />
        <Tooltip 
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
          labelFormatter={(label) => `Date: ${label}`}
          formatter={(value: any, name: string) => {
            if (name === 'Predicted Volume') {
              return [Math.round(value).toLocaleString(), 'Predicted Volume']
            }
            if (name === 'Lower Bound' || name === 'Upper Bound') {
              return [Math.round(value).toLocaleString(), name]
            }
            return [value, name]
          }}
        />
        <Legend />
        
        {/* Confidence Interval Area */}
        <Area
          type="monotone"
          dataKey="Upper Bound"
          stackId="confidence"
          stroke="none"
          fill="url(#confidence)"
          fillOpacity={0.3}
        />
        <Area
          type="monotone"
          dataKey="Lower Bound"
          stackId="confidence"
          stroke="none"
          fill="white"
          fillOpacity={1}
        />
        
        {/* Prediction Line */}
        <Line
          type="monotone"
          dataKey="Predicted Volume"
          stroke="#3b82f6"
          strokeWidth={3}
          dot={{ fill: '#3b82f6', strokeWidth: 2, r: 5 }}
          activeDot={{ r: 7, stroke: '#1d4ed8', strokeWidth: 2 }}
        />
        
        {/* Confidence Bounds */}
        <Line
          type="monotone"
          dataKey="Lower Bound"
          stroke="#8b5cf6"
          strokeWidth={1}
          strokeDasharray="5 5"
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="Upper Bound"
          stroke="#8b5cf6"
          strokeWidth={1}
          strokeDasharray="5 5"
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
} 