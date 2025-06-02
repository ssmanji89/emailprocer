'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Escalation } from '@/types/api'
import { apiClient } from '@/lib/api-client'
import { formatDistanceToNow } from 'date-fns'
import { cn } from '@/lib/utils'
import {
  X,
  AlertTriangle,
  RefreshCw,
  Mail,
  MessageSquare,
  ArrowRight,
  Timer,
  Users,
  CheckCircle,
} from 'lucide-react'

interface EscalationDetailModalProps {
  isOpen: boolean
  onClose: () => void
  escalation: Escalation
  onRefetch: () => void
}

interface AssignmentFormData {
  teamId: string
  notes: string
}

interface ResolutionFormData {
  notes: string
}

export function EscalationDetailModal({ 
  isOpen, 
  onClose, 
  escalation, 
  onRefetch 
}: EscalationDetailModalProps) {
  const [showAssignmentForm, setShowAssignmentForm] = useState(false)
  const [showResolutionForm, setShowResolutionForm] = useState(false)
  const [newPriority, setNewPriority] = useState(escalation.priority)
  const [assignmentData, setAssignmentData] = useState<AssignmentFormData>({
    teamId: escalation.team_id || '',
    notes: '',
  })
  const [resolutionData, setResolutionData] = useState<ResolutionFormData>({
    notes: '',
  })

  const { data: escalationDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['escalation-detail', escalation.escalation_id],
    queryFn: () => apiClient.getEscalationDetails(escalation.escalation_id),
    enabled: isOpen,
  })

  const { data: teamPerformance } = useQuery({
    queryKey: ['team-performance'],
    queryFn: () => apiClient.getTeamPerformance('all', '7d'),
    enabled: isOpen,
  })

  const assignMutation = useMutation({
    mutationFn: (data: AssignmentFormData) => 
      apiClient.assignEscalation(escalation.escalation_id, data.teamId),
    onSuccess: () => {
      setShowAssignmentForm(false)
      setAssignmentData({ teamId: '', notes: '' })
      onRefetch()
    },
  })

  const priorityMutation = useMutation({
    mutationFn: (priority: string) => 
      apiClient.updateEscalationPriority(escalation.escalation_id, priority),
    onSuccess: () => {
      onRefetch()
    },
  })

  const resolveMutation = useMutation({
    mutationFn: (data: ResolutionFormData) => 
      apiClient.resolveEscalation(escalation.escalation_id, data.notes),
    onSuccess: () => {
      setShowResolutionForm(false)
      setResolutionData({ notes: '' })
      onRefetch()
      onClose()
    },
  })

  const handleAssignmentSubmit = () => {
    assignMutation.mutate(assignmentData)
  }

  const handlePriorityUpdate = () => {
    if (newPriority !== escalation.priority) {
      priorityMutation.mutate(newPriority)
    }
  }

  const handleResolutionSubmit = () => {
    resolveMutation.mutate(resolutionData)
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
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
    switch (status) {
      case 'resolved':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'open':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'closed':
        return 'bg-gray-100 text-gray-800 border-gray-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getSLAStatus = () => {
    const now = new Date()
    const slaDate = new Date(escalation.sla_due_at)
    const timeDiff = slaDate.getTime() - now.getTime()
    
    if (timeDiff < 0) {
      return { status: 'overdue', color: 'text-red-600', text: 'Overdue' }
    } else if (timeDiff < 2 * 60 * 60 * 1000) { // 2 hours
      return { status: 'warning', color: 'text-orange-600', text: 'Due Soon' }
    } else {
      return { status: 'ok', color: 'text-green-600', text: 'On Track' }
    }
  }

  const slaStatus = getSLAStatus()

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            <h2 className="text-xl font-semibold">Escalation Details</h2>
            <Badge className={cn('border', getPriorityColor(escalation.priority))}>
              {escalation.priority.toUpperCase()}
            </Badge>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {detailLoading ? (
            <div className="flex items-center justify-center h-32">
              <RefreshCw className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <>
              {/* Escalation Overview */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    Escalation Overview
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium">Escalation ID</Label>
                      <div className="text-sm mt-1 font-mono">{escalation.escalation_id}</div>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Email ID</Label>
                      <div className="text-sm mt-1 font-mono">{escalation.email_id}</div>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Status</Label>
                      <div className="mt-1">
                        <Badge className={cn('border', getStatusColor(escalation.status))}>
                          {escalation.status.replace('_', ' ').toUpperCase()}
                        </Badge>
                      </div>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">SLA Status</Label>
                      <div className={cn('text-sm mt-1 font-medium', slaStatus.color)}>
                        {slaStatus.text}
                      </div>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Created</Label>
                      <div className="text-sm mt-1">
                        {formatDistanceToNow(new Date(escalation.created_at), { addSuffix: true })}
                        <div className="text-xs text-muted-foreground">
                          {new Date(escalation.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">SLA Due</Label>
                      <div className="text-sm mt-1">
                        {formatDistanceToNow(new Date(escalation.sla_due_at), { addSuffix: true })}
                        <div className="text-xs text-muted-foreground">
                          {new Date(escalation.sla_due_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">Escalation Reason</Label>
                    <div className="text-sm mt-1 p-3 bg-gray-50 rounded-md border">
                      {escalation.escalation_reason}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Related Email Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Mail className="h-5 w-5" />
                    Related Email
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <Label className="text-sm font-medium">From</Label>
                      <div className="text-sm mt-1">{escalation.sender_email}</div>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Subject</Label>
                      <div className="text-sm mt-1 font-medium">{escalation.email_subject}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Team Assignment */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Team Assignment
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {escalation.team_name ? (
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{escalation.team_name}</div>
                        {escalation.assigned_to && (
                          <div className="text-sm text-muted-foreground">
                            Assigned to: {escalation.assigned_to}
                          </div>
                        )}
                        {escalation.assigned_at && (
                          <div className="text-xs text-muted-foreground">
                            Assigned {formatDistanceToNow(new Date(escalation.assigned_at), { addSuffix: true })}
                          </div>
                        )}
                      </div>
                      <Button
                        variant="outline"
                        onClick={() => setShowAssignmentForm(true)}
                      >
                        Reassign
                      </Button>
                    </div>
                  ) : (
                    <div>
                      <p className="text-muted-foreground mb-3">No team assigned</p>
                      <Button onClick={() => setShowAssignmentForm(true)}>
                        Assign Team
                      </Button>
                    </div>
                  )}

                  {showAssignmentForm && (
                    <div className="mt-4 p-4 border rounded-lg bg-gray-50">
                      <h4 className="font-medium mb-3">Assign to Team</h4>
                      <div className="space-y-3">
                        <div>
                          <Label className="text-sm font-medium">Team</Label>
                          <select
                            value={assignmentData.teamId}
                            onChange={(e) => setAssignmentData(prev => ({ ...prev, teamId: e.target.value }))}
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          >
                            <option value="">Select a team</option>
                            {teamPerformance?.map((team) => (
                              <option key={team.team_id} value={team.team_id}>
                                {team.team_name} ({team.active_escalations} active)
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            onClick={handleAssignmentSubmit}
                            disabled={!assignmentData.teamId || assignMutation.isPending}
                          >
                            {assignMutation.isPending ? 'Assigning...' : 'Assign'}
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => setShowAssignmentForm(false)}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Priority Management */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Timer className="h-5 w-5" />
                    Priority Management
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <div>
                      <Label className="text-sm font-medium">Current Priority</Label>
                      <Badge className={cn('border ml-2', getPriorityColor(escalation.priority))}>
                        {escalation.priority.toUpperCase()}
                      </Badge>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    <div className="flex items-center gap-2">
                      <select
                        value={newPriority}
                        onChange={(e) => setNewPriority(e.target.value as any)}
                        className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                      </select>
                      <Button
                        onClick={handlePriorityUpdate}
                        disabled={newPriority === escalation.priority || priorityMutation.isPending}
                        size="sm"
                      >
                        {priorityMutation.isPending ? 'Updating...' : 'Update'}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Resolution */}
              {escalation.status !== 'resolved' && escalation.status !== 'closed' && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5" />
                      Resolution
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {!showResolutionForm ? (
                      <Button onClick={() => setShowResolutionForm(true)}>
                        Mark as Resolved
                      </Button>
                    ) : (
                      <div className="space-y-4">
                        <div>
                          <Label className="text-sm font-medium">Resolution Notes</Label>
                          <textarea
                            value={resolutionData.notes}
                            onChange={(e) => setResolutionData(prev => ({ ...prev, notes: e.target.value }))}
                            placeholder="Describe how this escalation was resolved..."
                            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button
                            onClick={handleResolutionSubmit}
                            disabled={!resolutionData.notes.trim() || resolveMutation.isPending}
                          >
                            {resolveMutation.isPending ? 'Resolving...' : 'Resolve Escalation'}
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => setShowResolutionForm(false)}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Resolution Notes (if resolved) */}
              {escalation.resolution_notes && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <MessageSquare className="h-5 w-5" />
                      Resolution Notes
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-sm p-3 bg-green-50 rounded-md border border-green-200">
                      {escalation.resolution_notes}
                    </div>
                    {escalation.resolved_at && (
                      <div className="text-xs text-muted-foreground mt-2">
                        Resolved {formatDistanceToNow(new Date(escalation.resolved_at), { addSuffix: true })}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
} 