'use client'

import { useState, useMemo } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table } from '@/components/ui/table'
import { Escalation } from '@/types/api'
import {
  Clock,
  User,
  AlertTriangle,
  CheckCircle,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Eye,
  RefreshCw,
  Timer,
} from 'lucide-react'

interface EscalationsGridProps {
  escalations: Escalation[]
  isLoading: boolean
  onEscalationSelect: (escalation: Escalation) => void
  onRefetch: () => void
}

type SortField = 'created_at' | 'priority' | 'status' | 'sla_due_at' | 'team_name'
type SortDirection = 'asc' | 'desc'

const getPriorityColor = (priority: string) => {
  switch (priority.toLowerCase()) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-200'
    case 'high':
      return 'bg-orange-100 text-orange-800 border-orange-200'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    case 'low':
      return 'bg-green-100 text-green-800 border-green-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case 'open':
      return 'bg-blue-100 text-blue-800'
    case 'in_progress':
      return 'bg-yellow-100 text-yellow-800'
    case 'resolved':
      return 'bg-green-100 text-green-800'
    case 'closed':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getSLAStatus = (sla_due_at: string) => {
  const now = new Date()
  const due = new Date(sla_due_at)
  const diffHours = (due.getTime() - now.getTime()) / (1000 * 60 * 60)

  if (diffHours < 0) {
    return { status: 'overdue', color: 'text-red-600', icon: AlertTriangle }
  } else if (diffHours < 2) {
    return { status: 'urgent', color: 'text-orange-600', icon: Timer }
  } else if (diffHours < 24) {
    return { status: 'due-soon', color: 'text-yellow-600', icon: Clock }
  } else {
    return { status: 'ok', color: 'text-green-600', icon: CheckCircle }
  }
}

export function EscalationsGrid({
  escalations,
  isLoading,
  onEscalationSelect,
}: EscalationsGridProps) {
  const [sortField, setSortField] = useState<SortField>('created_at')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedEscalations = useMemo(() => {
    if (!escalations.length) return []
    
    return [...escalations].sort((a, b) => {
      let aValue: string | number = a[sortField as keyof Escalation] as string | number
      let bValue: string | number = b[sortField as keyof Escalation] as string | number
      
      if (sortField === 'created_at' || sortField === 'sla_due_at') {
        aValue = new Date(aValue).getTime()
        bValue = new Date(bValue).getTime()
      }
      
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
      return 0
    })
  }, [escalations, sortField, sortDirection])

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ArrowUpDown className="h-4 w-4" />
    return sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading escalations...</p>
        </div>
      </div>
    )
  }

  if (!escalations.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-4" />
          <p className="text-muted-foreground">No active escalations</p>
          <p className="text-sm text-muted-foreground mt-2">
            All escalations have been resolved
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <thead>
            <tr className="border-b">
              <th className="text-left p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('created_at')}
                  className="flex items-center gap-2 font-medium"
                >
                  Created
                  <SortIcon field="created_at" />
                </Button>
              </th>
              <th className="text-left p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('priority')}
                  className="flex items-center gap-2 font-medium"
                >
                  Priority
                  <SortIcon field="priority" />
                </Button>
              </th>
              <th className="text-left p-4">Email Subject</th>
              <th className="text-left p-4">Reason</th>
              <th className="text-left p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('team_name')}
                  className="flex items-center gap-2 font-medium"
                >
                  Assigned Team
                  <SortIcon field="team_name" />
                </Button>
              </th>
              <th className="text-left p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('status')}
                  className="flex items-center gap-2 font-medium"
                >
                  Status
                  <SortIcon field="status" />
                </Button>
              </th>
              <th className="text-left p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('sla_due_at')}
                  className="flex items-center gap-2 font-medium"
                >
                  SLA Status
                  <SortIcon field="sla_due_at" />
                </Button>
              </th>
              <th className="text-right p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedEscalations.map((escalation) => {
              const slaStatus = getSLAStatus(escalation.sla_due_at)
              const SLAIcon = slaStatus.icon

              return (
                <tr
                  key={escalation.escalation_id}
                  className="border-b hover:bg-muted/50 cursor-pointer"
                  onClick={() => onEscalationSelect(escalation)}
                >
                  <td className="p-4">
                    <div className="text-sm">
                      {formatDistanceToNow(new Date(escalation.created_at), { addSuffix: true })}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(escalation.created_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="p-4">
                    <Badge className={getPriorityColor(escalation.priority)}>
                      {escalation.priority.toUpperCase()}
                    </Badge>
                  </td>
                  <td className="p-4">
                    <div className="text-sm font-medium max-w-xs truncate" title={escalation.email_subject}>
                      {escalation.email_subject}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      From: {escalation.sender_email}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="text-sm max-w-xs truncate" title={escalation.escalation_reason}>
                      {escalation.escalation_reason}
                    </div>
                  </td>
                  <td className="p-4">
                    {escalation.team_name ? (
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4" />
                        <span className="text-sm">{escalation.team_name}</span>
                      </div>
                    ) : (
                      <span className="text-sm text-muted-foreground">Unassigned</span>
                    )}
                  </td>
                  <td className="p-4">
                    <Badge className={getStatusColor(escalation.status)}>
                      {escalation.status.replace('_', ' ').toUpperCase()}
                    </Badge>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <SLAIcon className={`h-4 w-4 ${slaStatus.color}`} />
                      <div className="text-sm">
                        <div className={slaStatus.color}>
                          {slaStatus.status === 'overdue' ? 'Overdue' : 
                           slaStatus.status === 'urgent' ? 'Due Soon' :
                           slaStatus.status === 'due-soon' ? 'Due Today' : 'On Track'}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(escalation.sla_due_at), { addSuffix: true })}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex gap-1 justify-end">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation()
                          onEscalationSelect(escalation)
                        }}
                        title="View Details"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </Table>
      </div>
    </div>
  )
} 