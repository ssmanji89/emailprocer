'use client'

import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { EmailSearchForm } from '@/components/forms/email-search-form'
import { EmailHistoryTable } from '@/components/tables/email-history-table'
import { EmailDetailModal } from '@/components/modals/email-detail-modal'
import { apiClient } from '@/lib/api-client'
import { EmailHistoryParams, EmailHistoryItem } from '@/types/api'
import { formatNumber } from '@/lib/utils'
import { Mail, Search, Download, RefreshCw, AlertTriangle } from 'lucide-react'

export default function EmailHistoryPage() {
  const [searchParams, setSearchParams] = useState<EmailHistoryParams>({
    limit: 50,
    page: 1,
  })
  const [selectedEmail, setSelectedEmail] = useState<EmailHistoryItem | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [selectedEmails, setSelectedEmails] = useState<string[]>([])

  const { data: emailHistory, isLoading, error, refetch } = useQuery({
    queryKey: ['email-history', searchParams],
    queryFn: () => apiClient.getEmailHistory(searchParams),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const handleSearch = (filters: EmailHistoryParams) => {
    setSearchParams({
      ...filters,
      limit: 50,
      page: 1,
    })
  }

  const handlePageChange = (page: number) => {
    setSearchParams(prev => ({ ...prev, page }))
  }

  const handleEmailSelect = (email: EmailHistoryItem) => {
    setSelectedEmail(email)
    setIsDetailModalOpen(true)
  }

  const handleBulkSelect = (emailIds: string[]) => {
    setSelectedEmails(emailIds)
  }

  const handleExport = async (format: 'csv' | 'pdf' = 'csv') => {
    try {
      const blob = await apiClient.exportEmailHistory(searchParams, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = `email-history-${new Date().toISOString().split('T')[0]}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  const summaryStats = useMemo(() => {
    if (!emailHistory) return null
    
    const emails = emailHistory.emails
    const totalEmails = emailHistory.total_count
    const processedEmails = emails.filter(email => email.processing_status === 'completed').length
    const escalatedEmails = emails.filter(email => email.escalated).length
    const avgConfidence = emails.reduce((sum, email) => sum + (email.confidence_score || 0), 0) / emails.length

    return {
      totalEmails,
      processedEmails,
      escalatedEmails,
      avgConfidence: isNaN(avgConfidence) ? 0 : avgConfidence,
      successRate: emails.length > 0 ? (processedEmails / emails.length) * 100 : 0,
    }
  }, [emailHistory])

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-4" />
          <p className="text-red-500">Failed to load email history</p>
          <p className="text-sm text-muted-foreground mt-2">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <Button onClick={() => refetch()} className="mt-4">
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Email History & Search</h1>
          <p className="text-muted-foreground">
            Search and analyze your email processing history
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refetch()}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExport('csv')}
            className="flex items-center gap-2"
            disabled={!emailHistory?.emails.length}
          >
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExport('pdf')}
            className="flex items-center gap-2"
            disabled={!emailHistory?.emails.length}
          >
            <Download className="h-4 w-4" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* Search Interface */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Advanced Search
          </CardTitle>
          <CardDescription>
            Search emails by sender, subject, content, date range, and classification details
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmailSearchForm
            onSearch={handleSearch}
            initialFilters={searchParams}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>

      {/* Summary Statistics */}
      {summaryStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Emails</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(summaryStats.totalEmails)}
              </div>
              <p className="text-xs text-muted-foreground">
                In current search
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Processed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {formatNumber(summaryStats.processedEmails)}
              </div>
              <p className="text-xs text-muted-foreground">
                Successfully processed
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {summaryStats.successRate.toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                Processing success
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Escalated</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {formatNumber(summaryStats.escalatedEmails)}
              </div>
              <p className="text-xs text-muted-foreground">
                Required escalation
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(summaryStats.avgConfidence * 100).toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                Classification confidence
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Email History Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email History
            {emailHistory && (
              <span className="text-sm font-normal text-muted-foreground">
                ({formatNumber(emailHistory.total_count)} total)
              </span>
            )}
          </CardTitle>
          {selectedEmails.length > 0 && (
            <CardDescription>
              {selectedEmails.length} email(s) selected
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <EmailHistoryTable
            emails={emailHistory?.emails || []}
            isLoading={isLoading}
            onEmailSelect={handleEmailSelect}
            onBulkSelect={handleBulkSelect}
            selectedEmails={selectedEmails}
            totalCount={emailHistory?.total_count || 0}
            currentPage={searchParams.page || 1}
            pageSize={searchParams.limit || 50}
            onPageChange={handlePageChange}
          />
        </CardContent>
      </Card>

      {/* Email Detail Modal */}
      {selectedEmail && (
        <EmailDetailModal
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false)
            setSelectedEmail(null)
          }}
          email={selectedEmail}
          onRefetch={refetch}
        />
      )}
    </div>
  )
} 