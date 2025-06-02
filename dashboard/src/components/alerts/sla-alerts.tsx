'use client'

import { useMemo } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Escalation } from '@/types/api'
import { AlertTriangle, Clock, Timer, CheckCircle, User } from 'lucide-react'

interface SLAAlertsProps {
  escalations: Escalation[]
}

export function SLAAlerts({ escalations }: SLAAlertsProps) {
  const urgentEscalations = useMemo(() => {
    const now = new Date()
    
    return escalations
      .filter(escalation => escalation.status === 'open' || escalation.status === 'in_progress')
      .map(escalation => {
        const dueDate = new Date(escalation.sla_due_at)
        const diffHours = (dueDate.getTime() - now.getTime()) / (1000 * 60 * 60)
        
        let urgencyLevel: 'overdue' | 'critical' | 'warning' | 'normal'
        let color: string
        let icon: any
        
        if (diffHours < 0) {
          urgencyLevel = 'overdue'
          color = 'text-red-600 bg-red-50 border-red-200'
          icon = AlertTriangle
        } else if (diffHours < 2) {
          urgencyLevel = 'critical'
          color = 'text-orange-600 bg-orange-50 border-orange-200'
          icon = Timer
        } else if (diffHours < 24) {
          urgencyLevel = 'warning'
          color = 'text-yellow-600 bg-yellow-50 border-yellow-200'
          icon = Clock
        } else {
          urgencyLevel = 'normal'
          color = 'text-green-600 bg-green-50 border-green-200'
          icon = CheckCircle
        }
        
        return {
          ...escalation,
          urgencyLevel,
          color,
          icon,
          diffHours,
        }
      })
      .filter(escalation => escalation.urgencyLevel !== 'normal')
      .sort((a, b) => a.diffHours - b.diffHours) // Most urgent first
  }, [escalations])

  if (urgentEscalations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            SLA Status
          </CardTitle>
          <CardDescription>
            All escalations are within SLA compliance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle className="h-4 w-4" />
            <span className="text-sm">No urgent escalations requiring attention</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-600" />
          SLA Alerts
          <Badge variant="outline" className="text-red-600">
            {urgentEscalations.length} requiring attention
          </Badge>
        </CardTitle>
        <CardDescription>
          Escalations approaching or past their SLA deadlines
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {urgentEscalations.map((escalation) => {
            const Icon = escalation.icon
            
            return (
              <div
                key={escalation.escalation_id}
                className={`p-4 rounded-lg border ${escalation.color}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Icon className="h-5 w-5" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-sm">
                          {escalation.email_subject}
                        </h4>
                        <Badge 
                          variant="outline" 
                          className={
                            escalation.priority === 'critical' ? 'border-red-300 text-red-700' :
                            escalation.priority === 'high' ? 'border-orange-300 text-orange-700' :
                            escalation.priority === 'medium' ? 'border-yellow-300 text-yellow-700' :
                            'border-green-300 text-green-700'
                          }
                        >
                          {escalation.priority.toUpperCase()}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        From: {escalation.sender_email}
                      </div>
                      <div className="text-xs mt-1">
                        {escalation.urgencyLevel === 'overdue' ? (
                          <span className="text-red-600 font-medium">
                            Overdue by {formatDistanceToNow(new Date(escalation.sla_due_at))}
                          </span>
                        ) : (
                          <span>
                            Due {formatDistanceToNow(new Date(escalation.sla_due_at), { addSuffix: true })}
                          </span>
                        )}
                      </div>
                      {escalation.team_name && (
                        <div className="flex items-center gap-1 mt-1">
                          <User className="h-3 w-3" />
                          <span className="text-xs">Assigned to: {escalation.team_name}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline">
                      View Details
                    </Button>
                    {escalation.urgencyLevel === 'overdue' && (
                      <Button size="sm" variant="default" className="bg-red-600 hover:bg-red-700">
                        Urgent Action
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
        
        {urgentEscalations.length > 3 && (
          <div className="mt-4 text-center">
            <Button variant="outline" size="sm">
              View All {urgentEscalations.length} Urgent Escalations
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 