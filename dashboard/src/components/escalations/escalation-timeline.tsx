'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { apiClient } from '@/lib/api-client'
import { formatDateTime, formatTimeAgo, getStatusColor } from '@/lib/utils'
import {
  Clock,
  User,
  MessageSquare,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  Plus,
  Send,
  Loader2,
  Activity,
  Users,
  Settings,
  FileText
} from 'lucide-react'

interface TimelineEvent {
  timestamp: string
  action: string
  user: string
  details?: string
}

interface EscalationTimelineProps {
  escalationId: string
  currentStatus: string
  onStatusUpdate?: () => void
}

export function EscalationTimeline({ 
  escalationId, 
  currentStatus, 
  onStatusUpdate 
}: EscalationTimelineProps) {
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isAddingComment, setIsAddingComment] = useState(false)
  const [newComment, setNewComment] = useState('')
  const [isSubmittingComment, setIsSubmittingComment] = useState(false)

  useEffect(() => {
    loadTimeline()
  }, [escalationId])

  const loadTimeline = async () => {
    setIsLoading(true)
    try {
      const history = await apiClient.getEscalationHistory(escalationId)
      setTimeline(history)
    } catch (error) {
      console.error('Failed to load escalation timeline:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddComment = async () => {
    if (!newComment.trim()) return

    setIsSubmittingComment(true)
    try {
      // Add comment to timeline (this would be an API call)
      const commentEvent: TimelineEvent = {
        timestamp: new Date().toISOString(),
        action: 'comment_added',
        user: 'Current User', // This would come from auth context
        details: newComment
      }

      setTimeline(prev => [commentEvent, ...prev])
      setNewComment('')
      setIsAddingComment(false)
      
      if (onStatusUpdate) {
        onStatusUpdate()
      }
    } catch (error) {
      console.error('Failed to add comment:', error)
    } finally {
      setIsSubmittingComment(false)
    }
  }

  const getActionIcon = (action: string) => {
    switch (action.toLowerCase()) {
      case 'escalation_created':
        return <AlertTriangle className="h-4 w-4 text-orange-600" />
      case 'assigned':
      case 'team_assigned':
        return <Users className="h-4 w-4 text-blue-600" />
      case 'status_changed':
        return <Activity className="h-4 w-4 text-purple-600" />
      case 'priority_changed':
        return <ArrowRight className="h-4 w-4 text-yellow-600" />
      case 'comment_added':
        return <MessageSquare className="h-4 w-4 text-green-600" />
      case 'resolved':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'teams_group_created':
        return <Users className="h-4 w-4 text-blue-600" />
      case 'document_attached':
        return <FileText className="h-4 w-4 text-gray-600" />
      case 'settings_updated':
        return <Settings className="h-4 w-4 text-gray-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-600" />
    }
  }

  const getActionTitle = (action: string) => {
    switch (action.toLowerCase()) {
      case 'escalation_created':
        return 'Escalation Created'
      case 'assigned':
      case 'team_assigned':
        return 'Team Assigned'
      case 'status_changed':
        return 'Status Updated'
      case 'priority_changed':
        return 'Priority Changed'
      case 'comment_added':
        return 'Comment Added'
      case 'resolved':
        return 'Escalation Resolved'
      case 'teams_group_created':
        return 'Teams Group Created'
      case 'document_attached':
        return 'Document Attached'
      case 'settings_updated':
        return 'Settings Updated'
      default:
        return 'Action Taken'
    }
  }

  const getActionColor = (action: string) => {
    switch (action.toLowerCase()) {
      case 'escalation_created':
        return 'border-orange-200 bg-orange-50'
      case 'assigned':
      case 'team_assigned':
        return 'border-blue-200 bg-blue-50'
      case 'status_changed':
        return 'border-purple-200 bg-purple-50'
      case 'priority_changed':
        return 'border-yellow-200 bg-yellow-50'
      case 'comment_added':
        return 'border-green-200 bg-green-50'
      case 'resolved':
        return 'border-green-200 bg-green-50'
      case 'teams_group_created':
        return 'border-blue-200 bg-blue-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin mr-2" />
            <span>Loading timeline...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Timeline
        </CardTitle>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsAddingComment(!isAddingComment)}
            className="flex items-center gap-2"
          >
            <Plus className="h-3 w-3" />
            Add Comment
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Add Comment Section */}
        {isAddingComment && (
          <Card className="border-dashed">
            <CardContent className="pt-4">
              <div className="space-y-3">
                <Textarea
                  placeholder="Add a comment about this escalation..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  rows={3}
                />
                <div className="flex gap-2">
                  <Button
                    onClick={handleAddComment}
                    disabled={!newComment.trim() || isSubmittingComment}
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    {isSubmittingComment ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Send className="h-3 w-3" />
                    )}
                    Add Comment
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setIsAddingComment(false)
                      setNewComment('')
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Timeline Events */}
        <div className="space-y-4">
          {timeline.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No timeline events yet</p>
            </div>
          ) : (
            timeline.map((event, index) => (
              <div
                key={index}
                className={`relative pl-8 pb-4 ${
                  index !== timeline.length - 1 ? 'border-l-2 border-gray-200' : ''
                }`}
              >
                {/* Timeline Dot */}
                <div 
                  className={`absolute left-0 top-0 -ml-2 w-4 h-4 rounded-full border-2 border-white ${
                    getActionColor(event.action)
                  } flex items-center justify-center`}
                >
                  <div className="w-2 h-2 rounded-full bg-current opacity-60" />
                </div>

                {/* Event Content */}
                <div className={`p-4 rounded-lg border ${getActionColor(event.action)}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      {getActionIcon(event.action)}
                      <div>
                        <h4 className="font-medium text-sm">
                          {getActionTitle(event.action)}
                        </h4>
                        <div className="flex items-center gap-2 text-xs text-gray-600">
                          <User className="h-3 w-3" />
                          <span>{event.user}</span>
                          <span>•</span>
                          <span title={formatDateTime(event.timestamp)}>
                            {formatTimeAgo(event.timestamp)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Event Details */}
                  {event.details && (
                    <div className="mt-3 p-3 bg-white rounded border border-gray-100">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {event.details}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Current Status Badge */}
        <div className="pt-4 border-t">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Current Status:</span>
            <Badge className={getStatusColor(currentStatus)}>
              {currentStatus.replace('_', ' ').toUpperCase()}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 