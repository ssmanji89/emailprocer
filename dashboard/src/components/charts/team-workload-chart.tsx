'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { formatNumber, formatDuration } from '@/lib/utils'
import { TeamPerformance } from '@/types/api'
import { Users, Clock, CheckCircle, TrendingUp } from 'lucide-react'

interface TeamWorkloadChartProps {
  data: TeamPerformance[]
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

export function TeamWorkloadChart({ data }: TeamWorkloadChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <div className="text-center">
          <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No team data available</p>
        </div>
      </div>
    )
  }

  const chartData = data.map((team, index) => ({
    ...team,
    color: COLORS[index % COLORS.length],
    workload_ratio: team.active_escalations / team.member_count,
    efficiency_score: team.sla_compliance_rate * (1 / Math.max(team.avg_resolution_time_hours, 1))
  }))

  const totalEscalations = data.reduce((sum, team) => sum + team.active_escalations, 0)
  const totalMembers = data.reduce((sum, team) => sum + team.member_count, 0)

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{data.length}</div>
          <div className="text-sm text-muted-foreground">Active Teams</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{formatNumber(totalMembers)}</div>
          <div className="text-sm text-muted-foreground">Total Members</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">{formatNumber(totalEscalations)}</div>
          <div className="text-sm text-muted-foreground">Active Escalations</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {totalMembers > 0 ? (totalEscalations / totalMembers).toFixed(1) : '0'}
          </div>
          <div className="text-sm text-muted-foreground">Avg per Member</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Workload Distribution Chart */}
        <div>
          <h4 className="font-semibold mb-4 flex items-center gap-2">
            <Users className="h-4 w-4" />
            Active Escalations by Team
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="team_name" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis />
                <Tooltip 
                  formatter={(value: number, name: string) => [
                    formatNumber(value),
                    name === 'active_escalations' ? 'Active Escalations' : 
                    name === 'member_count' ? 'Team Members' : 
                    'Workload Ratio'
                  ]}
                />
                <Bar 
                  dataKey="active_escalations" 
                  fill="#3b82f6" 
                  radius={[4, 4, 0, 0]}
                  name="active_escalations"
                />
                <Bar 
                  dataKey="member_count" 
                  fill="#10b981" 
                  radius={[4, 4, 0, 0]}
                  opacity={0.7}
                  name="member_count"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Escalation Distribution Pie Chart */}
        <div>
          <h4 className="font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Escalation Distribution
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="active_escalations"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: number) => [formatNumber(value), 'Escalations']}
                  labelFormatter={(label) => `${label}`}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Team Performance Details */}
      <div>
        <h4 className="font-semibold mb-4 flex items-center gap-2">
          <CheckCircle className="h-4 w-4" />
          Team Performance Overview
        </h4>
        <div className="space-y-3">
          {chartData.map((team) => (
            <div key={team.team_id} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div 
                    className="w-4 h-4 rounded-full" 
                    style={{ backgroundColor: team.color }}
                  />
                  <h5 className="font-medium">{team.team_name}</h5>
                  <Badge variant="outline">
                    {formatNumber(team.member_count)} members
                  </Badge>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>{formatNumber(team.active_escalations)} active</span>
                  <span>{formatNumber(team.resolved_today)} resolved today</span>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span>SLA Compliance</span>
                    <span className="font-medium">{team.sla_compliance_rate.toFixed(1)}%</span>
                  </div>
                  <Progress 
                    value={team.sla_compliance_rate} 
                    className="h-2"
                  />
                </div>
                
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span>Workload per Member</span>
                    <span className="font-medium">{team.workload_ratio.toFixed(1)}</span>
                  </div>
                  <Progress 
                    value={Math.min(team.workload_ratio * 20, 100)} 
                    className="h-2"
                  />
                </div>
                
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4" />
                  <span>Avg Resolution:</span>
                  <span className="font-medium">
                    {formatDuration(team.avg_resolution_time_hours * 3600)}
                  </span>
                </div>
              </div>

              {/* Performance Trend */}
              {team.performance_trend && team.performance_trend.length > 0 && (
                <div className="mt-3 pt-3 border-t">
                  <div className="text-xs text-muted-foreground mb-2">Recent Performance Trend</div>
                  <div className="flex items-center gap-2">
                    {team.performance_trend.slice(-7).map((trend, index) => (
                      <div key={index} className="text-center">
                        <div className="text-xs font-medium">{trend.resolved_count}</div>
                        <div className="text-xs text-muted-foreground">
                          {new Date(trend.date).toLocaleDateString('en-US', { weekday: 'short' })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
} 