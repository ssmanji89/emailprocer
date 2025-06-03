'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Progress } from '@/components/ui/progress'
import { apiClient } from '@/lib/api-client'
import { formatDate, formatDateTime, downloadBlob, getLocalStorageItem, setLocalStorageItem } from '@/lib/utils'
import {
  Download,
  FileText,
  BarChart3,
  Calendar as CalendarIcon,
  Settings,
  Clock,
  RefreshCw,
  Save,
  Trash2,
  Eye,
  Send,
  Filter,
  Table,
  PieChart,
  Loader2,
  CheckCircle,
  X,
  Archive,
  Mail,
  FileSpreadsheet,
  FileImage,
  Plus
} from 'lucide-react'

interface ReportTemplate {
  id: string
  name: string
  description: string
  type: 'summary' | 'detailed' | 'analytical' | 'custom'
  sections: string[]
  filters: ReportFilters
  schedule?: ReportSchedule
  createdAt: string
  lastGenerated?: string
}

interface ReportFilters {
  dateRange: {
    from: Date | null
    to: Date | null
  }
  status: string[]
  priority: string[]
  teams: string[]
  categories: string[]
  includeMetrics: boolean
  includeCharts: boolean
  includeRawData: boolean
}

interface ReportSchedule {
  enabled: boolean
  frequency: 'daily' | 'weekly' | 'monthly'
  time: string
  recipients: string[]
  format: 'pdf' | 'csv' | 'xlsx'
}

interface ExportProgress {
  isGenerating: boolean
  progress: number
  currentStep: string
  totalSteps: number
  completed: boolean
  downloadUrl?: string
  error?: string
}

const REPORT_SECTIONS = [
  { id: 'executive_summary', label: 'Executive Summary', description: 'High-level overview and key metrics' },
  { id: 'escalation_trends', label: 'Escalation Trends', description: 'Volume and pattern analysis' },
  { id: 'team_performance', label: 'Team Performance', description: 'Team-wise metrics and comparisons' },
  { id: 'sla_compliance', label: 'SLA Compliance', description: 'SLA metrics and breach analysis' },
  { id: 'resolution_analysis', label: 'Resolution Analysis', description: 'Time to resolve and patterns' },
  { id: 'customer_satisfaction', label: 'Customer Satisfaction', description: 'Feedback and satisfaction scores' },
  { id: 'detailed_data', label: 'Detailed Data', description: 'Raw escalation data and logs' },
  { id: 'appendix', label: 'Appendix', description: 'Additional charts and supporting data' }
]

const PREDEFINED_TEMPLATES: Omit<ReportTemplate, 'id' | 'createdAt'>[] = [
  {
    name: 'Daily Operations Report',
    description: 'Quick daily overview for operational teams',
    type: 'summary',
    sections: ['executive_summary', 'escalation_trends', 'sla_compliance'],
    filters: {
      dateRange: { from: null, to: null },
      status: [],
      priority: [],
      teams: [],
      categories: [],
      includeMetrics: true,
      includeCharts: true,
      includeRawData: false
    }
  },
  {
    name: 'Weekly Management Report',
    description: 'Comprehensive weekly report for management',
    type: 'analytical',
    sections: ['executive_summary', 'escalation_trends', 'team_performance', 'sla_compliance', 'customer_satisfaction'],
    filters: {
      dateRange: { from: null, to: null },
      status: [],
      priority: [],
      teams: [],
      categories: [],
      includeMetrics: true,
      includeCharts: true,
      includeRawData: false
    }
  },
  {
    name: 'Complete Analysis Report',
    description: 'Full detailed report with all available data',
    type: 'detailed',
    sections: ['executive_summary', 'escalation_trends', 'team_performance', 'sla_compliance', 'resolution_analysis', 'customer_satisfaction', 'detailed_data', 'appendix'],
    filters: {
      dateRange: { from: null, to: null },
      status: [],
      priority: [],
      teams: [],
      categories: [],
      includeMetrics: true,
      includeCharts: true,
      includeRawData: true
    }
  }
]

export function ExportReportingSystem() {
  const [templates, setTemplates] = useState<ReportTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null)
  const [isCreatingTemplate, setIsCreatingTemplate] = useState(false)
  const [newTemplate, setNewTemplate] = useState<Partial<ReportTemplate>>({
    name: '',
    description: '',
    type: 'summary',
    sections: [],
    filters: {
      dateRange: { from: null, to: null },
      status: [],
      priority: [],
      teams: [],
      categories: [],
      includeMetrics: true,
      includeCharts: false,
      includeRawData: false
    }
  })
  const [exportFormat, setExportFormat] = useState<'pdf' | 'csv' | 'xlsx'>('pdf')
  const [exportProgress, setExportProgress] = useState<ExportProgress | null>(null)
  const [scheduledReports, setScheduledReports] = useState<ReportTemplate[]>([])

  useEffect(() => {
    loadTemplates()
    loadScheduledReports()
  }, [])

  const loadTemplates = () => {
    const saved = getLocalStorageItem<ReportTemplate[]>('report-templates', [])
    const withPredefined = [
      ...PREDEFINED_TEMPLATES.map(template => ({
        ...template,
        id: template.name.toLowerCase().replace(/\s+/g, '-'),
        createdAt: new Date().toISOString()
      })),
      ...saved
    ]
    setTemplates(withPredefined)
  }

  const loadScheduledReports = () => {
    const scheduled = templates.filter(t => t.schedule?.enabled)
    setScheduledReports(scheduled)
  }

  const saveTemplate = () => {
    if (!newTemplate.name || !newTemplate.description) return

    const template: ReportTemplate = {
      ...newTemplate as ReportTemplate,
      id: Date.now().toString(),
      createdAt: new Date().toISOString()
    }

    const updatedTemplates = [...templates, template]
    setTemplates(updatedTemplates)
    
    const customTemplates = updatedTemplates.filter(t => 
      !PREDEFINED_TEMPLATES.some(p => p.name === t.name)
    )
    setLocalStorageItem('report-templates', customTemplates)
    
    setIsCreatingTemplate(false)
    setNewTemplate({
      name: '',
      description: '',
      type: 'summary',
      sections: [],
      filters: {
        dateRange: { from: null, to: null },
        status: [],
        priority: [],
        teams: [],
        categories: [],
        includeMetrics: true,
        includeCharts: false,
        includeRawData: false
      }
    })
  }

  const deleteTemplate = (templateId: string) => {
    const updatedTemplates = templates.filter(t => t.id !== templateId)
    setTemplates(updatedTemplates)
    
    const customTemplates = updatedTemplates.filter(t => 
      !PREDEFINED_TEMPLATES.some(p => p.name === t.name)
    )
    setLocalStorageItem('report-templates', customTemplates)
    
    if (selectedTemplate?.id === templateId) {
      setSelectedTemplate(null)
    }
  }

  const generateReport = async (template: ReportTemplate, format: 'pdf' | 'csv' | 'xlsx') => {
    setExportProgress({
      isGenerating: true,
      progress: 0,
      currentStep: 'Initializing report generation...',
      totalSteps: 6,
      completed: false
    })

    try {
      // Step 1: Validate parameters
      await new Promise(resolve => setTimeout(resolve, 500))
      setExportProgress(prev => prev ? {
        ...prev,
        progress: 16,
        currentStep: 'Validating report parameters...'
      } : null)

      // Step 2: Fetch data
      await new Promise(resolve => setTimeout(resolve, 1000))
      setExportProgress(prev => prev ? {
        ...prev,
        progress: 33,
        currentStep: 'Fetching escalation data...'
      } : null)

      // Step 3: Process metrics
      await new Promise(resolve => setTimeout(resolve, 800))
      setExportProgress(prev => prev ? {
        ...prev,
        progress: 50,
        currentStep: 'Processing metrics and analytics...'
      } : null)

      // Step 4: Generate charts
      if (template.filters.includeCharts) {
        await new Promise(resolve => setTimeout(resolve, 1200))
        setExportProgress(prev => prev ? {
          ...prev,
          progress: 66,
          currentStep: 'Generating charts and visualizations...'
        } : null)
      }

      // Step 5: Compile report
      await new Promise(resolve => setTimeout(resolve, 1000))
      setExportProgress(prev => prev ? {
        ...prev,
        progress: 83,
        currentStep: 'Compiling report sections...'
      } : null)

      // Step 6: Generate final file
      await new Promise(resolve => setTimeout(resolve, 800))
      setExportProgress(prev => prev ? {
        ...prev,
        progress: 100,
        currentStep: 'Finalizing export...'
      } : null)

      // Simulate file generation
      const reportData = generateMockReportData(template)
      const blob = new Blob([JSON.stringify(reportData, null, 2)], { 
        type: format === 'pdf' ? 'application/pdf' : 
             format === 'xlsx' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' :
             'text/csv'
      })
      
      const filename = `${template.name.toLowerCase().replace(/\s+/g, '-')}-${new Date().toISOString().split('T')[0]}.${format}`
      downloadBlob(blob, filename)

      setExportProgress(prev => prev ? {
        ...prev,
        completed: true,
        currentStep: 'Report downloaded successfully!'
      } : null)

      // Update last generated timestamp
      const updatedTemplates = templates.map(t => 
        t.id === template.id ? { ...t, lastGenerated: new Date().toISOString() } : t
      )
      setTemplates(updatedTemplates)

    } catch (error) {
      setExportProgress(prev => prev ? {
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to generate report'
      } : null)
    }
  }

  const generateMockReportData = (template: ReportTemplate) => {
    return {
      title: template.name,
      generatedAt: new Date().toISOString(),
      template: template.name,
      sections: template.sections,
      summary: {
        totalEscalations: 142,
        resolvedEscalations: 128,
        averageResolutionTime: '4.2 hours',
        slaCompliance: '89.4%'
      },
      data: template.filters.includeRawData ? [
        { id: '1', subject: 'Sample escalation 1', status: 'resolved' },
        { id: '2', subject: 'Sample escalation 2', status: 'in_progress' }
      ] : [],
      charts: template.filters.includeCharts ? [
        { type: 'line', title: 'Escalation Trends', data: 'chart_data_placeholder' },
        { type: 'bar', title: 'Team Performance', data: 'chart_data_placeholder' }
      ] : []
    }
  }

  const previewReport = (template: ReportTemplate) => {
    alert(`Preview for: ${template.name}\n\nSections: ${template.sections.join(', ')}\nFilters: ${Object.keys(template.filters).length} filter(s) applied`)
  }

  const scheduleReport = (template: ReportTemplate, schedule: ReportSchedule) => {
    const updatedTemplate = { ...template, schedule }
    const updatedTemplates = templates.map(t => 
      t.id === template.id ? updatedTemplate : t
    )
    setTemplates(updatedTemplates)
    
    // Save to localStorage
    const customTemplates = updatedTemplates.filter(t => 
      !PREDEFINED_TEMPLATES.some(p => p.name === t.name)
    )
    setLocalStorageItem('report-templates', customTemplates)
    
    loadScheduledReports()
  }

  const toggleSection = (sectionId: string) => {
    setNewTemplate(prev => ({
      ...prev,
      sections: prev.sections?.includes(sectionId)
        ? prev.sections.filter(s => s !== sectionId)
        : [...(prev.sections || []), sectionId]
    }))
  }

  const getTemplateTypeIcon = (type: string) => {
    switch (type) {
      case 'summary': return <BarChart3 className="h-4 w-4" />
      case 'detailed': return <FileText className="h-4 w-4" />
      case 'analytical': return <PieChart className="h-4 w-4" />
      default: return <Settings className="h-4 w-4" />
    }
  }

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf': return <FileText className="h-4 w-4 text-red-600" />
      case 'csv': return <FileSpreadsheet className="h-4 w-4 text-green-600" />
      case 'xlsx': return <Table className="h-4 w-4 text-blue-600" />
      default: return <FileText className="h-4 w-4" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Export & Reporting System
            </CardTitle>
            <Button
              onClick={() => setIsCreatingTemplate(true)}
              className="flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Create Template
            </Button>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Report Templates */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Report Templates</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedTemplate?.id === template.id 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'hover:bg-gray-50'
                    }`}
                    onClick={() => setSelectedTemplate(template)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          {getTemplateTypeIcon(template.type)}
                          <h4 className="font-medium">{template.name}</h4>
                          <Badge variant="outline" className="text-xs">
                            {template.type}
                          </Badge>
                          {template.schedule?.enabled && (
                            <Badge variant="secondary" className="text-xs">
                              <Clock className="h-3 w-3 mr-1" />
                              Scheduled
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <span>{template.sections.length} sections</span>
                          <span>Created {formatDate(template.createdAt)}</span>
                          {template.lastGenerated && (
                            <span>Last generated {formatDate(template.lastGenerated)}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            previewReport(template)
                          }}
                        >
                          <Eye className="h-3 w-3" />
                        </Button>
                        {!PREDEFINED_TEMPLATES.some(p => p.name === template.name) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteTemplate(template.id)
                            }}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Create Template Form */}
          {isCreatingTemplate && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Create New Template</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Template Name</Label>
                    <Input
                      placeholder="Enter template name..."
                      value={newTemplate.name || ''}
                      onChange={(e) => setNewTemplate(prev => ({ ...prev, name: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Type</Label>
                    <Select 
                      value={newTemplate.type} 
                      onValueChange={(value: any) => setNewTemplate(prev => ({ ...prev, type: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="summary">Summary</SelectItem>
                        <SelectItem value="detailed">Detailed</SelectItem>
                        <SelectItem value="analytical">Analytical</SelectItem>
                        <SelectItem value="custom">Custom</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea
                    placeholder="Describe the purpose of this report..."
                    value={newTemplate.description || ''}
                    onChange={(e) => setNewTemplate(prev => ({ ...prev, description: e.target.value }))}
                    rows={2}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Report Sections</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {REPORT_SECTIONS.map((section) => (
                      <div key={section.id} className="flex items-start space-x-2">
                        <Checkbox
                          checked={newTemplate.sections?.includes(section.id)}
                          onCheckedChange={() => toggleSection(section.id)}
                        />
                        <div className="grid gap-1.5 leading-none">
                          <label className="text-sm font-medium leading-none">
                            {section.label}
                          </label>
                          <p className="text-xs text-gray-600">
                            {section.description}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <Label>Options</Label>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        checked={newTemplate.filters?.includeMetrics}
                        onCheckedChange={(checked) => setNewTemplate(prev => ({
                          ...prev,
                          filters: { ...prev.filters!, includeMetrics: checked as boolean }
                        }))}
                      />
                      <label className="text-sm">Include metrics and KPIs</label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        checked={newTemplate.filters?.includeCharts}
                        onCheckedChange={(checked) => setNewTemplate(prev => ({
                          ...prev,
                          filters: { ...prev.filters!, includeCharts: checked as boolean }
                        }))}
                      />
                      <label className="text-sm">Include charts and visualizations</label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        checked={newTemplate.filters?.includeRawData}
                        onCheckedChange={(checked) => setNewTemplate(prev => ({
                          ...prev,
                          filters: { ...prev.filters!, includeRawData: checked as boolean }
                        }))}
                      />
                      <label className="text-sm">Include raw data tables</label>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 pt-4 border-t">
                  <Button onClick={saveTemplate} disabled={!newTemplate.name || !newTemplate.description}>
                    <Save className="h-4 w-4 mr-2" />
                    Save Template
                  </Button>
                  <Button variant="outline" onClick={() => setIsCreatingTemplate(false)}>
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Export Panel */}
        <div className="space-y-4">
          {/* Quick Export */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Export</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedTemplate ? (
                <>
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <h4 className="font-medium text-blue-900">{selectedTemplate.name}</h4>
                    <p className="text-sm text-blue-700">{selectedTemplate.description}</p>
                    <div className="text-xs text-blue-600 mt-1">
                      {selectedTemplate.sections.length} sections included
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Export Format</Label>
                    <div className="grid grid-cols-3 gap-2">
                      {['pdf', 'csv', 'xlsx'].map((format) => (
                        <Button
                          key={format}
                          variant={exportFormat === format ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setExportFormat(format as any)}
                          className="flex items-center gap-2"
                        >
                          {getFormatIcon(format)}
                          {format.toUpperCase()}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <Button
                    className="w-full"
                    onClick={() => generateReport(selectedTemplate, exportFormat)}
                    disabled={exportProgress?.isGenerating}
                  >
                    {exportProgress?.isGenerating ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Download className="h-4 w-4 mr-2" />
                        Generate Report
                      </>
                    )}
                  </Button>
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>Select a template to export</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Export Progress */}
          {exportProgress && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Export Progress</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{exportProgress.currentStep}</span>
                    <span>{Math.round(exportProgress.progress)}%</span>
                  </div>
                  <Progress value={exportProgress.progress} />
                </div>

                {exportProgress.completed && (
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    <span className="text-sm">Report generated successfully!</span>
                  </div>
                )}

                {exportProgress.error && (
                  <div className="flex items-center gap-2 text-red-600">
                    <X className="h-4 w-4" />
                    <span className="text-sm">{exportProgress.error}</span>
                  </div>
                )}

                {(exportProgress.completed || exportProgress.error) && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExportProgress(null)}
                    className="w-full"
                  >
                    Close
                  </Button>
                )}
              </CardContent>
            </Card>
          )}

          {/* Scheduled Reports */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Scheduled Reports
              </CardTitle>
            </CardHeader>
            <CardContent>
              {scheduledReports.length === 0 ? (
                <div className="text-center py-6 text-gray-500">
                  <Archive className="h-6 w-6 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No scheduled reports</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {scheduledReports.map((report) => (
                    <div key={report.id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-sm">{report.name}</h4>
                          <p className="text-xs text-gray-600">
                            {report.schedule?.frequency} at {report.schedule?.time}
                          </p>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {report.schedule?.format?.toUpperCase()}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 