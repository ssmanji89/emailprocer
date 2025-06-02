'use client'

import { useState, useMemo } from 'react'
import { Table } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { EmailHistoryItem } from '@/types/api'
import { formatDistanceToNow } from 'date-fns'
import {
  Eye,
  MessageSquare,
  RefreshCw,
  AlertTriangle,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

interface EmailHistoryTableProps {
  emails: EmailHistoryItem[]
  isLoading: boolean
  onEmailSelect: (email: EmailHistoryItem) => void
  onBulkSelect: (emailIds: string[]) => void
  selectedEmails: string[]
  totalCount: number
  currentPage: number
  pageSize: number
  onPageChange: (page: number) => void
}

type SortField = 'received_datetime' | 'sender_email' | 'subject' | 'confidence_score' | 'processing_status'
type SortDirection = 'asc' | 'desc'

const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'bg-green-100 text-green-800'
    case 'processing':
      return 'bg-blue-100 text-blue-800'
    case 'failed':
      return 'bg-red-100 text-red-800'
    case 'pending':
      return 'bg-yellow-100 text-yellow-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getCategoryColor = (category?: string) => {
  if (!category) return 'bg-gray-100 text-gray-800'
  
  switch (category.toLowerCase()) {
    case 'support':
      return 'bg-blue-100 text-blue-800'
    case 'sales':
      return 'bg-green-100 text-green-800'
    case 'complaint':
      return 'bg-red-100 text-red-800'
    case 'spam':
      return 'bg-orange-100 text-orange-800'
    default:
      return 'bg-purple-100 text-purple-800'
  }
}

export function EmailHistoryTable({
  emails,
  isLoading,
  onEmailSelect,
  onBulkSelect,
  selectedEmails,
  totalCount,
  currentPage,
  pageSize,
  onPageChange,
}: EmailHistoryTableProps) {
  const [sortField, setSortField] = useState<SortField>('received_datetime')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [selectAll, setSelectAll] = useState(false)

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedEmails = useMemo(() => {
    if (!emails.length) return []
    
    return [...emails].sort((a, b) => {
      let aValue: any = a[sortField]
      let bValue: any = b[sortField]
      
      if (sortField === 'received_datetime') {
        aValue = new Date(aValue).getTime()
        bValue = new Date(bValue).getTime()
      }
      
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
      return 0
    })
  }, [emails, sortField, sortDirection])

  const handleSelectAll = () => {
    if (selectAll) {
      onBulkSelect([])
      setSelectAll(false)
    } else {
      onBulkSelect(emails.map(email => email.id))
      setSelectAll(true)
    }
  }

  const handleSelectEmail = (emailId: string) => {
    const newSelected = selectedEmails.includes(emailId)
      ? selectedEmails.filter(id => id !== emailId)
      : [...selectedEmails, emailId]
    
    onBulkSelect(newSelected)
    setSelectAll(newSelected.length === emails.length)
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ArrowUpDown className="h-4 w-4" />
    return sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
  }

  const totalPages = Math.ceil(totalCount / pageSize)
  const hasNextPage = currentPage < totalPages
  const hasPrevPage = currentPage > 1

  if (isLoading && !emails.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading email history...</p>
        </div>
      </div>
    )
  }

  if (!emails.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <MessageSquare className="h-8 w-8 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No emails found</p>
          <p className="text-sm text-muted-foreground mt-2">
            Try adjusting your search filters
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
              <th className="w-12 p-4">
                <input
                  type="checkbox"
                  checked={selectAll}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300"
                />
              </th>
              <th className="text-left p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('received_datetime')}
                  className="flex items-center gap-2 font-medium"
                >
                  Date Received
                  <SortIcon field="received_datetime" />
                </Button>
              </th>
              <th className="text-left p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('sender_email')}
                  className="flex items-center gap-2 font-medium"
                >
                  Sender
                  <SortIcon field="sender_email" />
                </Button>
              </th>
              <th className="text-left p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('subject')}
                  className="flex items-center gap-2 font-medium"
                >
                  Subject
                  <SortIcon field="subject" />
                </Button>
              </th>
              <th className="text-left p-4">Category</th>
              <th className="text-left p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('confidence_score')}
                  className="flex items-center gap-2 font-medium"
                >
                  Confidence
                  <SortIcon field="confidence_score" />
                </Button>
              </th>
              <th className="text-left p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('processing_status')}
                  className="flex items-center gap-2 font-medium"
                >
                  Status
                  <SortIcon field="processing_status" />
                </Button>
              </th>
              <th className="text-left p-4">Processing Time</th>
              <th className="text-right p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedEmails.map((email) => (
              <tr
                key={email.id}
                className="border-b hover:bg-muted/50 cursor-pointer"
                onClick={() => onEmailSelect(email)}
              >
                <td className="p-4">
                  <input
                    type="checkbox"
                    checked={selectedEmails.includes(email.id)}
                    onChange={(e) => {
                      e.stopPropagation()
                      handleSelectEmail(email.id)
                    }}
                    className="rounded border-gray-300"
                  />
                </td>
                <td className="p-4">
                  <div className="text-sm">
                    {formatDistanceToNow(new Date(email.received_datetime), { addSuffix: true })}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(email.received_datetime).toLocaleDateString()}
                  </div>
                </td>
                <td className="p-4">
                  <div className="text-sm font-medium">{email.sender_email}</div>
                </td>
                <td className="p-4">
                  <div className="text-sm max-w-xs truncate" title={email.subject}>
                    {email.subject}
                  </div>
                </td>
                <td className="p-4">
                  {email.category && (
                    <Badge className={getCategoryColor(email.category)}>
                      {email.category}
                    </Badge>
                  )}
                </td>
                <td className="p-4">
                  {email.confidence_score !== undefined && (
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${email.confidence_score * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {(email.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </td>
                <td className="p-4">
                  <Badge className={getStatusColor(email.processing_status)}>
                    {email.processing_status}
                  </Badge>
                  {email.escalated && (
                    <AlertTriangle className="h-4 w-4 text-orange-500 ml-2 inline" />
                  )}
                </td>
                <td className="p-4">
                  <div className="text-sm">
                    {email.processing_duration_seconds.toFixed(2)}s
                  </div>
                </td>
                <td className="p-4 text-right">
                  <div className="flex gap-1 justify-end">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation()
                        onEmailSelect(email)
                      }}
                      title="View Details"
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          Showing {(currentPage - 1) * pageSize + 1} to{' '}
          {Math.min(currentPage * pageSize, totalCount)} of {totalCount} emails
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={!hasPrevPage}
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>
          
          <span className="text-sm">
            Page {currentPage} of {totalPages}
          </span>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={!hasNextPage}
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
} 