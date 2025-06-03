'use client'

import { useState, useEffect, useMemo } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Escalation } from '@/types/api'
import { apiClient } from '@/lib/api-client'
import { teamsService } from '@/lib/teams-integration'
import { formatNumber, getStatusColor } from '@/lib/utils'
import {
  User,
  Users,
  Clock,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Search,
  Star,
  Zap,
  Activity,
  Brain,
  X
} from 'lucide-react'

interface TeamMemberSuggestion {
  userId: string
  displayName: string
  email: string
  expertise: string[]
  currentWorkload: number
  availability: 'available' | 'busy' | 'away'
  recommendationScore: number
}

interface TeamAssignmentModalProps {
  escalation: Escalation | null
  isOpen: boolean
  onClose: () => void
  onAssigned: () => void
}

export function TeamAssignmentModal({
  escalation,
  isOpen,
  onClose,
  onAssigned
}: TeamAssignmentModalProps) {
  const [suggestions, setSuggestions] = useState<TeamMemberSuggestion[]>([])
  const [selectedMembers, setSelectedMembers] = useState<string[]>([])
  const [assignmentNotes, setAssignmentNotes] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isAssigning, setIsAssigning] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [createTeamsGroup, setCreateTeamsGroup] = useState(true)

  // Load team member suggestions when modal opens
  useEffect(() => {
    if (isOpen && escalation) {
      loadTeamSuggestions()
    }
  }, [isOpen, escalation])

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setSelectedMembers([])
      setAssignmentNotes('')
      setSearchQuery('')
      setCreateTeamsGroup(true)
    }
  }, [isOpen])

  const loadTeamSuggestions = async () => {
    if (!escalation) return

    setIsLoading(true)
    try {
      const teamSuggestions = await teamsService.getTeamMemberSuggestions(escalation)
      setSuggestions(teamSuggestions)
    } catch (error) {
      console.error('Failed to load team suggestions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredSuggestions = useMemo(() => {
    if (!searchQuery) return suggestions

    return suggestions.filter(member =>
      member.displayName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.expertise.some(skill => 
        skill.toLowerCase().includes(searchQuery.toLowerCase())
      )
    )
  }, [suggestions, searchQuery])

  const selectedMemberDetails = useMemo(() => {
    return selectedMembers.map(memberId => 
      suggestions.find(s => s.userId === memberId)
    ).filter(Boolean) as TeamMemberSuggestion[]
  }, [selectedMembers, suggestions])

  const handleMemberToggle = (memberId: string) => {
    setSelectedMembers(prev => 
      prev.includes(memberId)
        ? prev.filter(id => id !== memberId)
        : [...prev, memberId]
    )
  }

  const handleAssignment = async () => {
    if (!escalation || selectedMembers.length === 0) return

    setIsAssigning(true)
    try {
      // Assign escalation to selected team members
      await apiClient.assignEscalation(escalation.escalation_id, {
        assigned_to: selectedMembers.join(','),
        notes: assignmentNotes
      })

      // Create Teams group if requested
      if (createTeamsGroup && selectedMembers.length > 0) {
        const memberEmails = selectedMemberDetails.map(m => m.email)
        await teamsService.createEscalationGroup(escalation, memberEmails)
      }

      onAssigned()
      onClose()
    } catch (error) {
      console.error('Failed to assign escalation:', error)
    } finally {
      setIsAssigning(false)
    }
  }

  const getAvailabilityColor = (availability: string) => {
    switch (availability) {
      case 'available': return 'text-green-600'
      case 'busy': return 'text-yellow-600'
      case 'away': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getRecommendationBadge = (score: number) => {
    if (score >= 80) return { label: 'Highly Recommended', color: 'bg-green-100 text-green-800' }
    if (score >= 60) return { label: 'Recommended', color: 'bg-blue-100 text-blue-800' }
    if (score >= 40) return { label: 'Suitable', color: 'bg-yellow-100 text-yellow-800' }
    return { label: 'Available', color: 'bg-gray-100 text-gray-800' }
  }

  const getTotalWorkload = () => {
    return selectedMemberDetails.reduce((total, member) => total + member.currentWorkload, 0)
  }

  const getTeamExpertise = () => {
    const allExpertise = selectedMemberDetails.flatMap(member => member.expertise)
    const uniqueExpertise = Array.from(new Set(allExpertise))
    return uniqueExpertise.slice(0, 8) // Limit to 8 skills for display
  }

  if (!escalation) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Assign Team Members
          </DialogTitle>
          <DialogDescription>
            Select team members to handle this escalation based on expertise and workload
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Escalation Summary */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Escalation Details</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Subject:</span> {escalation.email_subject}
                </div>
                <div>
                  <span className="font-medium">Priority:</span>{' '}
                  <Badge className={getStatusColor(escalation.priority)}>
                    {escalation.priority.toUpperCase()}
                  </Badge>
                </div>
                <div>
                  <span className="font-medium">From:</span> {escalation.sender_email}
                </div>
                <div>
                  <span className="font-medium">Reason:</span> {escalation.escalation_reason}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Team Member Search */}
          <div className="space-y-3">
            <Label>Search Team Members</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by name, email, or expertise..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Team Member Suggestions */}
          <div className="space-y-3">
            <Label>Available Team Members</Label>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin" />
                <span className="ml-2">Loading team suggestions...</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-64 overflow-y-auto">
                {filteredSuggestions.map((member) => {
                  const isSelected = selectedMembers.includes(member.userId)
                  const recommendation = getRecommendationBadge(member.recommendationScore)

                  return (
                    <Card 
                      key={member.userId}
                      className={`cursor-pointer transition-all ${
                        isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                      }`}
                      onClick={() => handleMemberToggle(member.userId)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                <User className="h-4 w-4 text-blue-600" />
                              </div>
                              <div>
                                <p className="font-medium text-sm">{member.displayName}</p>
                                <p className="text-xs text-gray-500">{member.email}</p>
                              </div>
                            </div>

                            <div className="mt-3 space-y-2">
                              <div className="flex items-center gap-2">
                                <Activity className={`h-3 w-3 ${getAvailabilityColor(member.availability)}`} />
                                <span className="text-xs capitalize">{member.availability}</span>
                                <span className="text-xs text-gray-500">•</span>
                                <span className="text-xs">{formatNumber(member.currentWorkload)} active</span>
                              </div>

                              <div className="flex items-center gap-1">
                                <Star className="h-3 w-3 text-yellow-500" />
                                <span className="text-xs">{member.recommendationScore}% match</span>
                              </div>

                              <div className="flex flex-wrap gap-1">
                                {member.expertise.slice(0, 3).map((skill) => (
                                  <Badge key={skill} variant="outline" className="text-xs">
                                    {skill}
                                  </Badge>
                                ))}
                                {member.expertise.length > 3 && (
                                  <Badge variant="outline" className="text-xs">
                                    +{member.expertise.length - 3} more
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="flex flex-col items-end gap-2">
                            <Badge className={recommendation.color}>
                              {recommendation.label}
                            </Badge>
                            {isSelected && (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            )}
          </div>

          {/* Selected Team Summary */}
          {selectedMembers.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Selected Team ({selectedMembers.length} members)
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0 space-y-4">
                <div className="flex flex-wrap gap-2">
                  {selectedMemberDetails.map((member) => (
                    <Badge 
                      key={member.userId} 
                      variant="outline" 
                      className="flex items-center gap-1"
                    >
                      {member.displayName}
                      <X 
                        className="h-3 w-3 cursor-pointer hover:text-red-600" 
                        onClick={(e) => {
                          e.stopPropagation()
                          handleMemberToggle(member.userId)
                        }}
                      />
                    </Badge>
                  ))}
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-blue-600" />
                    <span>Total Workload: {getTotalWorkload()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Brain className="h-4 w-4 text-purple-600" />
                    <span>Skills: {getTeamExpertise().length}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-yellow-600" />
                    <span>Avg Match: {Math.round(selectedMemberDetails.reduce((sum, m) => sum + m.recommendationScore, 0) / selectedMemberDetails.length)}%</span>
                  </div>
                </div>

                {getTeamExpertise().length > 0 && (
                  <div>
                    <Label className="text-xs">Combined Expertise</Label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {getTeamExpertise().map((skill) => (
                        <Badge key={skill} variant="secondary" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Assignment Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes">Assignment Notes</Label>
            <Textarea
              id="notes"
              placeholder="Add notes about the assignment, expected timeline, or specific instructions..."
              value={assignmentNotes}
              onChange={(e) => setAssignmentNotes(e.target.value)}
              rows={3}
            />
          </div>

          {/* Teams Integration Option */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="create-teams-group"
              checked={createTeamsGroup}
              onChange={(e) => setCreateTeamsGroup(e.target.checked)}
              className="rounded"
            />
            <Label htmlFor="create-teams-group" className="text-sm">
              Create Microsoft Teams group for collaboration
            </Label>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            onClick={handleAssignment}
            disabled={selectedMembers.length === 0 || isAssigning}
            className="flex items-center gap-2"
          >
            {isAssigning ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Assigning...
              </>
            ) : (
              <>
                <Users className="h-4 w-4" />
                Assign Team ({selectedMembers.length})
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 