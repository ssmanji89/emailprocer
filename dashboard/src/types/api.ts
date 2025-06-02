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

// Phase 6 Types - Advanced Analytics & Intelligence

// Trend Analysis Types
export interface TrendAnalytics {
  period_start: string;
  period_end: string;
  volume_trends: Array<{
    date: string;
    emails_received: number;
    emails_processed: number;
    processing_rate: number;
    avg_processing_time_ms: number;
  }>;
  seasonal_patterns: Array<{
    hour_of_day: number;
    avg_volume: number;
    peak_indicator: boolean;
  }>;
  category_trends: Array<{
    category: string;
    trend_data: Array<{
      date: string;
      count: number;
      growth_rate: number;
    }>;
  }>;
  performance_trends: Array<{
    date: string;
    success_rate: number;
    escalation_rate: number;
    avg_confidence: number;
    human_feedback_score: number;
  }>;
  forecasting: {
    next_7_days: Array<{
      date: string;
      predicted_volume: number;
      confidence_interval: {
        lower: number;
        upper: number;
      };
    }>;
    next_30_days_summary: {
      predicted_total: number;
      growth_rate: number;
      seasonal_factor: number;
    };
  };
}

export interface TrendParams {
  period?: '7d' | '30d' | '90d' | '6m' | '1y';
  granularity?: 'hour' | 'day' | 'week' | 'month';
  categories?: string[];
  include_forecast?: boolean;
  include_seasonality?: boolean;
}

// Performance Insights Types
export interface PerformanceInsights {
  efficiency_metrics: {
    overall_score: number;
    processing_efficiency: number;
    classification_accuracy: number;
    automation_rate: number;
    response_time_score: number;
  };
  bottlenecks: Array<{
    bottleneck_type: 'processing' | 'classification' | 'escalation' | 'team_capacity';
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    impact_score: number;
    affected_volume: number;
    recommendations: string[];
  }>;
  optimization_opportunities: Array<{
    opportunity_id: string;
    type: 'automation' | 'process_improvement' | 'resource_allocation';
    title: string;
    description: string;
    potential_savings_hours: number;
    implementation_effort: 'low' | 'medium' | 'high';
    roi_score: number;
  }>;
  team_insights: Array<{
    team_id: string;
    team_name: string;
    efficiency_score: number;
    workload_balance: number;
    skill_utilization: number;
    recommendations: string[];
  }>;
}

// Predictive Analytics Types
export interface PredictiveAnalytics {
  volume_predictions: {
    short_term: Array<{
      date: string;
      predicted_volume: number;
      confidence: number;
      factors: string[];
    }>;
    long_term: Array<{
      month: string;
      predicted_volume: number;
      trend_direction: 'up' | 'down' | 'stable';
      seasonal_adjustment: number;
    }>;
  };
  escalation_predictions: Array<{
    date: string;
    predicted_escalations: number;
    risk_factors: Array<{
      factor: string;
      impact_score: number;
    }>;
    prevention_recommendations: string[];
  }>;
  capacity_planning: {
    current_capacity: number;
    predicted_demand: number;
    capacity_gap: number;
    recommended_team_size: number;
    timeline_recommendations: Array<{
      period: string;
      action: string;
      priority: 'low' | 'medium' | 'high';
    }>;
  };
  pattern_evolution: Array<{
    pattern_type: string;
    trend_direction: 'emerging' | 'stable' | 'declining';
    confidence: number;
    impact_assessment: string;
    adaptation_suggestions: string[];
  }>;
}

// Custom Reports Types
export interface CustomReport {
  report_id: string;
  name: string;
  description: string;
  created_by: string;
  created_at: string;
  last_run: string;
  schedule?: {
    frequency: 'daily' | 'weekly' | 'monthly';
    time: string;
    recipients: string[];
  };
  config: {
    metrics: string[];
    filters: Record<string, any>;
    chart_types: string[];
    date_range: string;
  };
}

export interface ReportData {
  report_id: string;
  generated_at: string;
  data: Record<string, any>;
  charts: Array<{
    chart_id: string;
    type: string;
    title: string;
    data: any[];
  }>;
  summary: {
    key_insights: string[];
    recommendations: string[];
    alerts: string[];
  };
} 