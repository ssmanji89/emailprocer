// API Response Types for EmailBot Analytics

export interface ProcessingStats {
  emails_processed_today: number;
  emails_processed_total: number;
  processing_success_rate: number;
  avg_processing_time_seconds: number;
  active_processing_jobs: number;
  last_processing_run: string;
}

export interface ClassificationStats {
  total_classified: number;
  high_confidence_rate: number;
  avg_confidence_score: number;
  human_feedback_count: number;
  categories_identified: number;
}

export interface MetricsSummary {
  uptime_hours: number;
  emails_per_hour: number;
  escalation_rate: number;
  automation_rate: number;
  user_satisfaction_score: number;
}

export interface DashboardData {
  processing: ProcessingStats;
  classification: ClassificationStats;
  active_escalations: number;
  automation_opportunities: number;
  metrics: MetricsSummary;
}

export interface ProcessingAnalytics {
  period_days: number;
  overall: {
    total_processed: number;
    successful: number;
    failed: number;
    responses_sent: number;
    escalations_created: number;
    avg_processing_time_ms: number;
  };
  daily_trends: Array<{
    date: string;
    count: number;
    avg_time_ms: number;
  }>;
}

export interface ClassificationAnalytics {
  category_distribution: Array<{
    category: string;
    count: number;
    avg_confidence: number;
  }>;
  confidence_stats: {
    avg_confidence: number;
    min_confidence: number;
    max_confidence: number;
  };
  feedback_distribution: Array<{
    feedback: string;
    count: number;
  }>;
}

export interface PatternAnalytics {
  automation_candidates: Array<{
    pattern_id: string;
    pattern_type: string;
    description: string;
    frequency: number;
    automation_potential: number;
    time_savings_potential_minutes: number;
  }>;
}

export interface EmailHistoryItem {
  id: string;
  sender_email: string;
  subject: string;
  received_datetime: string;
  processed_datetime: string;
  processing_status: string;
  processing_duration_seconds: number;
  category?: string;
  confidence_score?: number;
  escalated?: boolean;
}

// Phase 5.4 Types - Email History & Search Interface
export interface EmailDetail extends EmailHistoryItem {
  content: string;
  thread_id?: string;
  attachments: Array<{
    filename: string;
    size: number;
    type: string;
  }>;
  classification_reasoning: string;
  processing_steps: Array<{
    step: string;
    timestamp: string;
    status: string;
    details?: string;
  }>;
  related_emails: EmailHistoryItem[];
}

export interface SearchFilters {
  sender?: string;
  subject?: string;
  content?: string;
  date_from?: string;
  date_to?: string;
  category?: string;
  status?: string;
  confidence_min?: number;
  confidence_max?: number;
}

export interface EmailHistory {
  emails: EmailHistoryItem[];
  total_count: number;
  page: number;
  limit: number;
}

// Phase 5.5 Types - Escalation Management System
export interface Escalation {
  escalation_id: string;
  email_id: string;
  team_id?: string;
  team_name?: string;
  assigned_to?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  created_at: string;
  assigned_at?: string;
  resolved_at?: string;
  sla_due_at: string;
  escalation_reason: string;
  resolution_notes?: string;
  email_subject: string;
  sender_email: string;
}

export interface TeamPerformance {
  team_id: string;
  team_name: string;
  member_count: number;
  active_escalations: number;
  avg_resolution_time_hours: number;
  sla_compliance_rate: number;
  resolved_today: number;
  resolved_this_week: number;
  performance_trend: Array<{
    date: string;
    resolved_count: number;
    avg_time_hours: number;
  }>;
}

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: {
    [key: string]: string | object;
  };
}

// Request types
export interface EmailHistoryParams {
  sender?: string;
  days?: number;
  limit?: number;
  page?: number;
  category?: string;
  status?: string;
  confidence_min?: number;
  confidence_max?: number;
  subject?: string;
  content?: string;
  date_from?: string;
  date_to?: string;
}

export interface PatternParams {
  min_frequency?: number;
  min_automation_potential?: number;
}

export interface FeedbackRequest {
  email_id: string;
  feedback: 'correct' | 'incorrect' | 'partially_correct';
  notes?: string;
}

// Dashboard specific types
export interface DashboardFilter {
  dateRange: '1d' | '7d' | '30d' | '90d';
  category?: string;
  status?: string;
}

export interface ChartDataPoint {
  date: string;
  count: number;
  label?: string;
  value?: number;
}

export interface NavigationItem {
  href: string;
  label: string;
  icon: string;
  active?: boolean;
} 