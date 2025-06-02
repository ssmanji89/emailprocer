'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  X, 
  Clock, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  BarChart3,
  Target,
  FileText
} from 'lucide-react'

interface PatternDetailModalProps {
  pattern: {
    pattern_id: string
    pattern_type: string
    description: string
    frequency: number
    automation_potential: number
    time_savings_potential_minutes: number
  }
  isOpen: boolean
  onClose: () => void
  onApprove: (patternId: string) => void
  onReject: (patternId: string) => void
}

export function PatternDetailModal({ 
  pattern, 
  isOpen, 
  onClose, 
  onApprove, 
  onReject 
}: PatternDetailModalProps) {
  const [approvalNotes, setApprovalNotes] = useState('')

  if (!isOpen) return null

  const formatTimeSavings = (minutes: number) => {
    if (minutes >= 60) {
      return `${(minutes / 60).toFixed(1)} hours`
    }
    return `${minutes} minutes`
  }

  const getAutomationPotentialColor = (potential: number) => {
    if (potential >= 90) return 'bg-green-100 text-green-800'
    if (potential >= 75) return 'bg-blue-100 text-blue-800'
    if (potential >= 60) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  const getRiskLevel = (potential: number) => {
    if (potential >= 90) return { level: 'Low', color: 'text-green-600' }
    if (potential >= 75) return { level: 'Medium', color: 'text-yellow-600' }
    return { level: 'High', color: 'text-red-600' }
  }

  const risk = getRiskLevel(pattern.automation_potential)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto bg-background rounded-lg shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold">Pattern Analysis</h2>
            <p className="text-muted-foreground">
              Detailed automation opportunity assessment
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {/* Pattern Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Pattern Overview
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Pattern Type</label>
                  <div className="mt-1">
                    <Badge variant="outline">{pattern.pattern_type}</Badge>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Pattern ID</label>
                  <div className="mt-1 font-mono text-sm">{pattern.pattern_id}</div>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Description</label>
                <div className="mt-1 p-3 bg-muted rounded-md">
                  {pattern.description}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Metrics */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Frequency</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{pattern.frequency}</div>
                <p className="text-xs text-muted-foreground">
                  emails matching this pattern
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Automation Potential</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{pattern.automation_potential.toFixed(1)}%</div>
                <Badge className={getAutomationPotentialColor(pattern.automation_potential)}>
                  {pattern.automation_potential >= 90 ? 'Excellent' : 
                   pattern.automation_potential >= 75 ? 'Good' : 
                   pattern.automation_potential >= 60 ? 'Fair' : 'Poor'}
                </Badge>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Time Savings</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatTimeSavings(pattern.time_savings_potential_minutes)}
                </div>
                <p className="text-xs text-muted-foreground">
                  potential per occurrence
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Risk Assessment */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Risk Assessment
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Implementation Risk</label>
                  <div className={`mt-1 font-medium ${risk.color}`}>
                    {risk.level} Risk
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Confidence Score</label>
                  <div className="mt-1 font-medium">
                    {pattern.automation_potential.toFixed(1)}% confidence
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ROI Projection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                ROI Projection
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Weekly Savings</label>
                  <div className="mt-1 text-lg font-bold">
                    {formatTimeSavings(pattern.time_savings_potential_minutes * pattern.frequency * 0.14)}
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Monthly Savings</label>
                  <div className="mt-1 text-lg font-bold">
                    {formatTimeSavings(pattern.time_savings_potential_minutes * pattern.frequency * 0.6)}
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Annual Savings</label>
                  <div className="mt-1 text-lg font-bold">
                    {formatTimeSavings(pattern.time_savings_potential_minutes * pattern.frequency * 7.3)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            <Button
              variant="outline"
              onClick={() => onReject(pattern.pattern_id)}
              className="text-red-600 hover:text-red-700"
            >
              <XCircle className="h-4 w-4 mr-2" />
              Reject
            </Button>
            <Button
              onClick={() => onApprove(pattern.pattern_id)}
              className="text-green-600 hover:text-green-700"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Approve for Automation
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
} 