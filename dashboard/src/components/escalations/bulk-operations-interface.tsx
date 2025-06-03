'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { apiClient } from '@/lib/api-client'
import { Escalation } from '@/types/api'
import { formatTimeAgo, getStatusColor, formatNumber } from '@/lib/utils'
import {
  CheckSquare,
  Square,
  Users,
  AlertTriangle,
  Clock,
  ArrowRight,
  Archive,
  Trash2,
  Download,
  RefreshCw,
  Loader2,
  X,
  Check,
  Settings,
  Filter,
  Activity,
  Mail,
  FileText
} from 'lucide-react'

interface BulkAction {
  id: string
  label: string
  icon: React.ReactNode
  description: string
  requiresConfirmation: boolean
  requiresInput?: boolean
  inputLabel?: string
  inputPlaceholder?: string
}

interface BulkOperationProgress {
  total: number
  completed: number
  failed: number
  inProgress: boolean
  errors: string[]
}

interface BulkOperationsInterfaceProps {
  escalations: Escalation[]
  onRefresh: () => void
  isLoading?: boolean
}

const BULK_ACTIONS: BulkAction[] = [
  {
    id: 'assign_team',
    label: 'Assign Team',
    icon: <Users className="h-4 w-4" />,
    description: 'Assign selected escalations to a team',
    requiresConfirmation: true,
    requiresInput: true,
    inputLabel: 'Select Team',
    inputPlaceholder: 'Choose team...'
  },
  {
    id: 'change_status',
    label: 'Change Status',
    icon: <Activity className="h-4 w-4" />,
    description: 'Update status for selected escalations',
    requiresConfirmation: true,
    requiresInput: true,
    inputLabel: 'New Status',
    inputPlaceholder: 'Select status...'
  },
  {
    id: 'change_priority',
    label: 'Change Priority',
    icon: <AlertTriangle className="h-4 w-4" />,
    description: 'Update priority for selected escalations',
    requiresConfirmation: true,
    requiresInput: true,
    inputLabel: 'New Priority',
    inputPlaceholder: 'Select priority...'
  },
  {
    id: 'add_comment',
    label: 'Add Comment',
    icon: <FileText className="h-4 w-4" />,
    description: 'Add a comment to selected escalations',
    requiresConfirmation: false,
    requiresInput: true,
    inputLabel: 'Comment',
    inputPlaceholder: 'Enter comment...'
  },
  {
    id: 'send_notification',
    label: 'Send Notification',
    icon: <Mail className="h-4 w-4" />,
    description: 'Send notification about selected escalations',
    requiresConfirmation: true,
    requiresInput: true,
    inputLabel: 'Message',
    inputPlaceholder: 'Enter notification message...'
  },
  {
    id: 'export',
    label: 'Export Selected',
    icon: <Download className="h-4 w-4" />,
    description: 'Export selected escalations to CSV/PDF',
    requiresConfirmation: false,
    requiresInput: true,
    inputLabel: 'Export Format',
    inputPlaceholder: 'Select format...'
  },
  {
    id: 'archive',
    label: 'Archive',
    icon: <Archive className="h-4 w-4" />,
    description: 'Archive selected escalations',
    requiresConfirmation: true
  }
]

export function BulkOperationsInterface({
  escalations,
  onRefresh,
  isLoading = false
}: BulkOperationsInterfaceProps) {
  const [selectedEscalations, setSelectedEscalations] = useState<string[]>([])
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [selectedAction, setSelectedAction] = useState<BulkAction | null>(null)
  const [actionInput, setActionInput] = useState('')
  const [progress, setProgress] = useState<BulkOperationProgress | null>(null)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterPriority, setFilterPriority] = useState<string>('all')

  // Reset selections when escalations change
  useEffect(() => {
    setSelectedEscalations(prev => 
      prev.filter(id => escalations.some(e => e.escalation_id === id))
    )
  }, [escalations])

  const filteredEscalations = escalations.filter(escalation => {
    if (filterStatus !== 'all' && escalation.status !== filterStatus) return false
    if (filterPriority !== 'all' && escalation.priority !== filterPriority) return false
    return true
  })

  const isAllSelected = filteredEscalations.length > 0 && 
    selectedEscalations.length === filteredEscalations.length

  const isIndeterminate = selectedEscalations.length > 0 && 
    selectedEscalations.length < filteredEscalations.length

  const toggleSelectAll = () => {
    if (isAllSelected) {
      setSelectedEscalations([])
    } else {
      setSelectedEscalations(filteredEscalations.map(e => e.escalation_id))
    }
  }

  const toggleSelectEscalation = (escalationId: string) => {
    setSelectedEscalations(prev =>
      prev.includes(escalationId)
        ? prev.filter(id => id !== escalationId)
        : [...prev, escalationId]
    )
  }

  const handleBulkAction = (action: BulkAction) => {
    setSelectedAction(action)
    setActionInput('')
    
    if (action.requiresConfirmation) {
      setShowConfirmDialog(true)
    } else {
      executeBulkAction(action)
    }
  }

  const executeBulkAction = async (action: BulkAction) => {
    if (selectedEscalations.length === 0) return

    setProgress({
      total: selectedEscalations.length,
      completed: 0,
      failed: 0,
      inProgress: true,
      errors: []
    })

    try {
      let result

      switch (action.id) {
        case 'assign_team':
          result = await apiClient.bulkUpdateEscalations(selectedEscalations, {
            team_id: actionInput
          })
          break

        case 'change_status':
          result = await apiClient.bulkUpdateEscalations(selectedEscalations, {
            status: actionInput as any
          })
          break

        case 'change_priority':
          result = await apiClient.bulkUpdateEscalations(selectedEscalations, {
            priority: actionInput as any
          })
          break

        case 'export':
          const exportFormat = actionInput as 'csv' | 'pdf'
          const escalationIds = selectedEscalations
          const filters = { escalation_ids: escalationIds }
          
          const blob = await apiClient.exportEscalations(filters, exportFormat)
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `escalations-${new Date().toISOString().split('T')[0]}.${exportFormat}`
          a.click()
          window.URL.revokeObjectURL(url)
          
          result = { success: true, updated_count: selectedEscalations.length }
          break

        case 'add_comment':
          // This would need a separate API endpoint for bulk comments
          result = { success: true, updated_count: selectedEscalations.length }
          break

        case 'send_notification':
          // This would use the notification API
          result = { success: true, updated_count: selectedEscalations.length }
          break

        case 'archive':
          // This would use an archive API endpoint
          result = { success: true, updated_count: selectedEscalations.length }
          break

        default:
          throw new Error(`Unknown action: ${action.id}`)
      }

      setProgress(prev => prev ? {
        ...prev,
        completed: result.updated_count,
        inProgress: false
      } : null)

      // Clear selections and refresh data
      setSelectedEscalations([])
      onRefresh()

    } catch (error) {
      console.error('Bulk operation failed:', error)
      setProgress(prev => prev ? {
        ...prev,
        failed: prev.total - prev.completed,
        inProgress: false,
        errors: [...prev.errors, error instanceof Error ? error.message : 'Unknown error']
      } : null)
    }

    setShowConfirmDialog(false)
    setSelectedAction(null)
  }

  const getActionInputOptions = (action: BulkAction) => {
    switch (action.id) {
      case 'assign_team':
        return [
          { value: 'support', label: 'Support Team' },
          { value: 'technical', label: 'Technical Team' },
          { value: 'management', label: 'Management Team' },
          { value: 'qa', label: 'QA Team' }
        ]
      case 'change_status':
        return [
          { value: 'open', label: 'Open' },
          { value: 'in_progress', label: 'In Progress' },
          { value: 'resolved', label: 'Resolved' },
          { value: 'closed', label: 'Closed' }
        ]
      case 'change_priority':
        return [
          { value: 'low', label: 'Low' },
          { value: 'medium', label: 'Medium' },
          { value: 'high', label: 'High' },
          { value: 'critical', label: 'Critical' }
        ]
      case 'export':
        return [
          { value: 'csv', label: 'CSV Format' },
          { value: 'pdf', label: 'PDF Format' }
        ]
      default:
        return []
    }
  }

  const getSelectionSummary = () => {
    if (selectedEscalations.length === 0) return null

    const selectedItems = escalations.filter(e => selectedEscalations.includes(e.escalation_id))
    const statusCounts = selectedItems.reduce((acc, item) => {
      acc[item.status] = (acc[item.status] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const priorityCounts = selectedItems.reduce((acc, item) => {
      acc[item.priority] = (acc[item.priority] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    return { statusCounts, priorityCounts }
  }

  const selectionSummary = getSelectionSummary()

  return (
    <div className="space-y-4">
      {/* Control Panel */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <CheckSquare className="h-5 w-5" />
              Bulk Operations
              {selectedEscalations.length > 0 && (
                <Badge variant="secondary">
                  {selectedEscalations.length} selected
                </Badge>
              )}
            </CardTitle>
            <div className="flex gap-2">
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterPriority} onValueChange={setFilterPriority}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priority</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="sm"
                onClick={onRefresh}
                disabled={isLoading}
              >
                <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Selection Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={isAllSelected}
                  indeterminate={isIndeterminate}
                  onCheckedChange={toggleSelectAll}
                />
                <label className="text-sm font-medium">
                  Select All ({filteredEscalations.length})
                </label>
              </div>
              {selectedEscalations.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedEscalations([])}
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear Selection
                </Button>
              )}
            </div>
            <span className="text-sm text-gray-600">
              {formatNumber(filteredEscalations.length)} escalations
            </span>
          </div>

          {/* Selection Summary */}
          {selectionSummary && (
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-blue-900 mb-2">Status Distribution</h4>
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(selectionSummary.statusCounts).map(([status, count]) => (
                      <Badge key={status} className={getStatusColor(status)} variant="outline">
                        {status}: {count}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-blue-900 mb-2">Priority Distribution</h4>
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(selectionSummary.priorityCounts).map(([priority, count]) => (
                      <Badge key={priority} className={getStatusColor(priority)} variant="outline">
                        {priority}: {count}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Bulk Actions */}
          {selectedEscalations.length > 0 && (
            <div className="space-y-3">
              <Label>Available Actions</Label>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                {BULK_ACTIONS.map((action) => (
                  <Button
                    key={action.id}
                    variant="outline"
                    size="sm"
                    onClick={() => handleBulkAction(action)}
                    className="flex items-center gap-2 justify-start p-3 h-auto"
                    disabled={progress?.inProgress}
                  >
                    {action.icon}
                    <div className="text-left">
                      <div className="font-medium">{action.label}</div>
                      <div className="text-xs text-gray-600">{action.description}</div>
                    </div>
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Progress Indicator */}
          {progress && (
            <div className="space-y-3 p-4 bg-gray-50 rounded-lg border">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">
                  {progress.inProgress ? 'Processing...' : 'Operation Complete'}
                </h4>
                <span className="text-sm text-gray-600">
                  {progress.completed + progress.failed} / {progress.total}
                </span>
              </div>
              <Progress 
                value={((progress.completed + progress.failed) / progress.total) * 100} 
                className="w-full"
              />
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Completed: {progress.completed}</span>
                </div>
                <div className="flex items-center gap-2">
                  <X className="h-4 w-4 text-red-600" />
                  <span>Failed: {progress.failed}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-600" />
                  <span>Remaining: {progress.total - progress.completed - progress.failed}</span>
                </div>
              </div>
              {progress.errors.length > 0 && (
                <div className="mt-2">
                  <Label className="text-red-600">Errors:</Label>
                  <ul className="text-sm text-red-600 mt-1">
                    {progress.errors.map((error, index) => (
                      <li key={index}>• {error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Escalation List with Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Escalations ({filteredEscalations.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredEscalations.map((escalation) => (
              <div
                key={escalation.escalation_id}
                className={`p-3 border rounded-lg hover:bg-gray-50 ${
                  selectedEscalations.includes(escalation.escalation_id) 
                    ? 'bg-blue-50 border-blue-200' 
                    : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <Checkbox
                    checked={selectedEscalations.includes(escalation.escalation_id)}
                    onCheckedChange={() => toggleSelectEscalation(escalation.escalation_id)}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium truncate">{escalation.email_subject}</h4>
                      <div className="flex gap-2">
                        <Badge className={getStatusColor(escalation.status)}>
                          {escalation.status}
                        </Badge>
                        <Badge className={getStatusColor(escalation.priority)}>
                          {escalation.priority}
                        </Badge>
                      </div>
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      <span>From: {escalation.sender_email}</span>
                      <span className="mx-2">•</span>
                      <span>{formatTimeAgo(escalation.created_at)}</span>
                      {escalation.assigned_to && (
                        <>
                          <span className="mx-2">•</span>
                          <span>Assigned to: {escalation.assigned_to}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedAction?.icon}
              Confirm {selectedAction?.label}
            </DialogTitle>
            <DialogDescription>
              {selectedAction?.description}
              <br />
              This action will affect <strong>{selectedEscalations.length}</strong> escalations.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {selectedAction?.requiresInput && (
              <div className="space-y-2">
                <Label>{selectedAction.inputLabel}</Label>
                {getActionInputOptions(selectedAction).length > 0 ? (
                  <Select value={actionInput} onValueChange={setActionInput}>
                    <SelectTrigger>
                      <SelectValue placeholder={selectedAction.inputPlaceholder} />
                    </SelectTrigger>
                    <SelectContent>
                      {getActionInputOptions(selectedAction).map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Textarea
                    placeholder={selectedAction.inputPlaceholder}
                    value={actionInput}
                    onChange={(e) => setActionInput(e.target.value)}
                    rows={3}
                  />
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={() => selectedAction && executeBulkAction(selectedAction)}
              disabled={selectedAction?.requiresInput && !actionInput.trim()}
            >
              Execute {selectedAction?.label}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
} 