'use client'

import { useMemo } from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'

interface TrendAnalysisChartProps {
  data: any[]
  type: 'volume' | 'performance'
  height?: number
}

export default function TrendAnalysisChart({ 
  data, 
  type, 
  height = 300 
}: TrendAnalysisChartProps) {
  const chartData = useMemo(() => {
    if (type === 'volume') {
      return data.map(item => ({
        date: new Date(item.date).toLocaleDateString(),
        'Emails Received': item.emails_received,
        'Emails Processed': item.emails_processed,
        'Processing Rate': item.processing_rate,
        'Avg Time (ms)': item.avg_processing_time_ms
      }))
    } else {
      return data.map(item => ({
        date: new Date(item.date).toLocaleDateString(),
        'Success Rate': (item.success_rate * 100).toFixed(1),
        'Escalation Rate': (item.escalation_rate * 100).toFixed(1),
        'Avg Confidence': (item.avg_confidence * 100).toFixed(1),
        'Feedback Score': (item.human_feedback_score * 100).toFixed(1)
      }))
    }
  }, [data, type])

  if (type === 'volume') {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="emailsReceived" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
            </linearGradient>
            <linearGradient id="emailsProcessed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
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
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="Emails Received"
            stackId="1"
            stroke="#3b82f6"
            fill="url(#emailsReceived)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="Emails Processed"
            stackId="1"
            stroke="#10b981"
            fill="url(#emailsProcessed)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
        <XAxis 
          dataKey="date" 
          tick={{ fontSize: 12 }}
          stroke="#6b7280"
        />
        <YAxis 
          tick={{ fontSize: 12 }}
          stroke="#6b7280"
          domain={[0, 100]}
        />
        <Tooltip 
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
          formatter={(value: any) => [`${value}%`, '']}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="Success Rate"
          stroke="#10b981"
          strokeWidth={2}
          dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Line
          type="monotone"
          dataKey="Escalation Rate"
          stroke="#ef4444"
          strokeWidth={2}
          dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Line
          type="monotone"
          dataKey="Avg Confidence"
          stroke="#8b5cf6"
          strokeWidth={2}
          dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Line
          type="monotone"
          dataKey="Feedback Score"
          stroke="#f59e0b"
          strokeWidth={2}
          dot={{ fill: '#f59e0b', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
} 