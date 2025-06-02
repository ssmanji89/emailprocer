'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { EmailHistoryItem } from '@/types/api'
import { apiClient } from '@/lib/api-client'
import { formatDistanceToNow } from 'date-fns'
import {
  X,
  Mail,
  Clock,
  User,
  Tag,
  AlertTriangle,
  RefreshCw,
  MessageSquare,
  CheckCircle,
  XCircle,
  Eye,
  Download,
  ArrowRight,
} from 'lucide-react'

interface EmailDetailModalProps {
  isOpen: boolean
  onClose: () => void
  email: EmailHistoryItem
  onRefetch: () => void
}

interface FeedbackFormData {
  feedback: 'correct' | 'incorrect' | 'partially_correct'
  notes: string
}

interface EscalationFormData {
  reason: string
}

export function EmailDetailModal({ isOpen, onClose, email, onRefetch }: EmailDetailModalProps) {
  const [showFeedbackForm, setShowFeedbackForm] = useState(false)
  const [showEscalationForm, setShowEscalationForm] = useState(false)
  const [feedbackData, setFeedbackData] = useState<FeedbackFormData>({
    feedback: 'correct',
    notes: '',
  })
  const [escalationData, setEscalationData] = useState<EscalationFormData>({
    reason: '',
  })

  const { data: emailDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['email-detail', email.id],
    queryFn: () => apiClient.getEmailDetails(email.id),
    enabled: isOpen,
  })

  const feedbackMutation = useMutation({
    mutationFn: (data: FeedbackFormData) => 
      apiClient.submitEmailFeedback(email.id, {
        email_id: email.id,
        feedback: data.feedback,
        notes: data.notes,
      }),
    onSuccess: () => {
      setShowFeedbackForm(false)
      setFeedbackData({ feedback: 'correct', notes: '' })
      onRefetch()
    },
  })

  const reprocessMutation = useMutation({
    mutationFn: () => apiClient.reprocessEmail(email.id),
    onSuccess: () => {
      onRefetch()
    },
  })

  const escalationMutation = useMutation({
    mutationFn: (data: EscalationFormData) => 
      apiClient.escalateEmail(email.id, data.reason),
    onSuccess: () => {
      setShowEscalationForm(false)
      setEscalationData({ reason: '' })
      onRefetch()
    },
  })

  const handleFeedbackSubmit = () => {
    feedbackMutation.mutate(feedbackData)
  }

  const handleReprocess = () => {
    reprocessMutation.mutate()
  }

  const handleEscalationSubmit = () => {
    escalationMutation.mutate(escalationData)
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />
      case 'processing':
        return <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
      default:
        return <Clock className="h-4 w-4 text-gray-600" />
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            <h2 className="text-xl font-semibold">Email Details</h2>
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
              {/* Email Header */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="h-5 w-5" />
                    Email Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium">From</Label>
                      <div className="text-sm mt-1">{email.sender_email}</div>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Received</Label>
                      <div className="text-sm mt-1">
                        {formatDistanceToNow(new Date(email.received_datetime), { addSuffix: true })}
                        <div className="text-xs text-muted-foreground">
                          {new Date(email.received_datetime).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="md:col-span-2">
                      <Label className="text-sm font-medium">Subject</Label>
                      <div className="text-sm mt-1 font-medium">{email.subject}</div>
                    </div>
                  </div>

                  {emailDetail?.attachments && emailDetail.attachments.length > 0 && (
                    <div>
                      <Label className="text-sm font-medium">Attachments</Label>
                      <div className="mt-1 space-y-1">
                        {emailDetail.attachments.map((attachment, index) => (
                          <div key={index} className="flex items-center gap-2 text-sm">
                            <Download className="h-4 w-4" />
                            {attachment.filename} ({attachment.size} bytes)
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Email Content */}
              {emailDetail?.content && (
                <Card>
                  <CardHeader>
                    <CardTitle>Email Content</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-gray-50 p-4 rounded-md border">
                      <pre className="whitespace-pre-wrap text-sm font-mono">
                        {emailDetail.content}
                      </pre>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Classification Results */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Tag className="h-5 w-5" />
                    Classification Results
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label className="text-sm font-medium">Category</Label>
                      <div className="mt-1">
                        {email.category ? (
                          <Badge>{email.category}</Badge>
                        ) : (
                          <span className="text-sm text-muted-foreground">Not classified</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Confidence Score</Label>
                      <div className="mt-1">
                        {email.confidence_score !== undefined ? (
                          <div className="flex items-center gap-2">
                            <div className="w-24 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${email.confidence_score * 100}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium">
                              {(email.confidence_score * 100).toFixed(1)}%
                            </span>
                          </div>
                        ) : (
                          <span className="text-sm text-muted-foreground">No confidence score</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Processing Status</Label>
                      <div className="mt-1 flex items-center gap-2">
                        {getStatusIcon(email.processing_status)}
                        <span className="text-sm capitalize">{email.processing_status}</span>
                        {email.escalated && (
                          <Badge variant="outline" className="text-orange-600">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Escalated
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>

                  {emailDetail?.classification_reasoning && (
                    <div>
                      <Label className="text-sm font-medium">Classification Reasoning</Label>
                      <div className="mt-1 text-sm bg-blue-50 p-3 rounded-md">
                        {emailDetail.classification_reasoning}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Processing Timeline */}
              {emailDetail?.processing_steps && emailDetail.processing_steps.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Clock className="h-5 w-5" />
                      Processing Timeline
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {emailDetail.processing_steps.map((step, index) => (
                        <div key={index} className="flex items-center gap-3">
                          <div className="flex-shrink-0">
                            {getStatusIcon(step.status)}
                          </div>
                          <div className="flex-1">
                            <div className="text-sm font-medium">{step.step}</div>
                            <div className="text-xs text-muted-foreground">
                              {formatDistanceToNow(new Date(step.timestamp), { addSuffix: true })}
                            </div>
                            {step.details && (
                              <div className="text-xs text-muted-foreground mt-1">
                                {step.details}
                              </div>
                            )}
                          </div>
                          {index < emailDetail.processing_steps.length - 1 && (
                            <ArrowRight className="h-4 w-4 text-muted-foreground" />
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Related Emails */}
              {emailDetail?.related_emails && emailDetail.related_emails.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Related Emails</CardTitle>
                    <CardDescription>
                      Other emails in this thread or with similar patterns
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {emailDetail.related_emails.map((relatedEmail) => (
                        <div key={relatedEmail.id} className="flex items-center justify-between p-2 border rounded">
                          <div>
                            <div className="text-sm font-medium">{relatedEmail.subject}</div>
                            <div className="text-xs text-muted-foreground">
                              From: {relatedEmail.sender_email} • {formatDistanceToNow(new Date(relatedEmail.received_datetime), { addSuffix: true })}
                            </div>
                          </div>
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Feedback Form */}
              {showFeedbackForm && (
                <Card>
                  <CardHeader>
                    <CardTitle>Provide Feedback</CardTitle>
                    <CardDescription>
                      Help improve the classification accuracy by providing feedback
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="feedback-type">Feedback Type</Label>
                      <Select
                        id="feedback-type"
                        value={feedbackData.feedback}
                        onChange={(e) => setFeedbackData(prev => ({ ...prev, feedback: e.target.value as any }))}
                      >
                        <option value="correct">Classification is correct</option>
                        <option value="incorrect">Classification is incorrect</option>
                        <option value="partially_correct">Classification is partially correct</option>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="feedback-notes">Additional Notes</Label>
                      <Input
                        id="feedback-notes"
                        placeholder="Optional notes about the classification..."
                        value={feedbackData.notes}
                        onChange={(e) => setFeedbackData(prev => ({ ...prev, notes: e.target.value }))}
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleFeedbackSubmit}
                        disabled={feedbackMutation.isPending}
                      >
                        {feedbackMutation.isPending ? 'Submitting...' : 'Submit Feedback'}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setShowFeedbackForm(false)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Escalation Form */}
              {showEscalationForm && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5" />
                      Create Escalation
                    </CardTitle>
                    <CardDescription>
                      Escalate this email for human review and resolution
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="escalation-reason">Escalation Reason</Label>
                      <Input
                        id="escalation-reason"
                        placeholder="Describe why this email needs escalation..."
                        value={escalationData.reason}
                        onChange={(e) => setEscalationData(prev => ({ ...prev, reason: e.target.value }))}
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleEscalationSubmit}
                        disabled={escalationMutation.isPending || !escalationData.reason.trim()}
                      >
                        {escalationMutation.isPending ? 'Creating...' : 'Create Escalation'}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setShowEscalationForm(false)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="border-t p-6 flex justify-between">
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setShowFeedbackForm(!showFeedbackForm)}
              className="flex items-center gap-2"
            >
              <MessageSquare className="h-4 w-4" />
              Provide Feedback
            </Button>
            <Button
              variant="outline"
              onClick={handleReprocess}
              disabled={reprocessMutation.isPending}
              className="flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              {reprocessMutation.isPending ? 'Reprocessing...' : 'Reprocess'}
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowEscalationForm(!showEscalationForm)}
              className="flex items-center gap-2"
            >
              <AlertTriangle className="h-4 w-4" />
              Escalate
            </Button>
          </div>
          <Button onClick={onClose}>Close</Button>
        </div>
      </div>
    </div>
  )
} 