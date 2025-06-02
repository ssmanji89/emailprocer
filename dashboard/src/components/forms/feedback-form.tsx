'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FeedbackRequest } from '@/types/api'
import { X, ThumbsUp, AlertTriangle, CheckCircle } from 'lucide-react'

interface FeedbackFormProps {
  onClose: () => void;
  onSubmit: (feedback: FeedbackRequest) => Promise<void>;
}

export function FeedbackForm({ onClose, onSubmit }: FeedbackFormProps) {
  const [formData, setFormData] = useState<{
    email_id: string;
    feedback: 'correct' | 'incorrect' | 'partially_correct';
    notes: string;
  }>({
    email_id: '',
    feedback: 'correct',
    notes: '',
  })
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.email_id.trim()) {
      setError('Email ID is required')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      await onSubmit({
        email_id: formData.email_id.trim(),
        feedback: formData.feedback,
        notes: formData.notes.trim() || undefined,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback')
    } finally {
      setIsSubmitting(false)
    }
  }

  const feedbackOptions = [
    {
      value: 'correct' as const,
      label: 'Correct',
      description: 'The AI classification was accurate',
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200'
    },
    {
      value: 'partially_correct' as const,
      label: 'Partially Correct',
      description: 'The classification was close but not perfect',
      icon: AlertTriangle,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200'
    },
    {
      value: 'incorrect' as const,
      label: 'Incorrect',
      description: 'The AI classification was wrong',
      icon: X,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200'
    }
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <Card className="border-0 shadow-none">
          <CardHeader className="pb-4">
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <ThumbsUp className="h-5 w-5" />
                  Submit Classification Feedback
                </CardTitle>
                <CardDescription>
                  Help improve AI classification accuracy
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email ID Input */}
              <div>
                <label htmlFor="email_id" className="block text-sm font-medium mb-2">
                  Email ID
                </label>
                <input
                  type="text"
                  id="email_id"
                  value={formData.email_id}
                  onChange={(e) => setFormData({ ...formData, email_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter the email ID to provide feedback for"
                  required
                />
              </div>

              {/* Feedback Selection */}
              <div>
                <label className="block text-sm font-medium mb-3">
                  Classification Accuracy
                </label>
                <div className="space-y-2">
                  {feedbackOptions.map((option) => {
                    const Icon = option.icon
                    const isSelected = formData.feedback === option.value
                    
                    return (
                      <label
                        key={option.value}
                        className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                          isSelected 
                            ? `${option.bgColor} ${option.borderColor} ${option.color}` 
                            : 'bg-white border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <input
                          type="radio"
                          name="feedback"
                          value={option.value}
                          checked={isSelected}
                          onChange={(e) => setFormData({ 
                            ...formData, 
                            feedback: e.target.value as typeof formData.feedback 
                          })}
                          className="sr-only"
                        />
                        <Icon className={`h-5 w-5 mt-0.5 ${isSelected ? option.color : 'text-gray-400'}`} />
                        <div>
                          <div className={`font-medium ${isSelected ? option.color : 'text-gray-900'}`}>
                            {option.label}
                          </div>
                          <div className={`text-sm ${isSelected ? option.color : 'text-gray-500'}`}>
                            {option.description}
                          </div>
                        </div>
                      </label>
                    )
                  })}
                </div>
              </div>

              {/* Notes (Optional) */}
              <div>
                <label htmlFor="notes" className="block text-sm font-medium mb-2">
                  Additional Notes <span className="text-gray-400">(Optional)</span>
                </label>
                <textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="Provide additional context or suggestions for improvement..."
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex items-center gap-2 text-red-800">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="text-sm font-medium">Error</span>
                  </div>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={onClose}
                  className="flex-1"
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <ThumbsUp className="h-4 w-4 mr-2" />
                      Submit Feedback
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 