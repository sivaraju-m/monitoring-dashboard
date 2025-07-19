# Monitoring Dashboard Terraform Variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "bigquery_location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "US"
}

variable "timezone" {
  description = "Timezone for scheduled jobs"
  type        = string
  default     = "America/New_York"
}

# Cloud Run Configuration
variable "cloud_run_cpu" {
  description = "CPU allocation for Cloud Run"
  type        = string
  default     = "2"
}

variable "cloud_run_memory" {
  description = "Memory allocation for Cloud Run"
  type        = string
  default     = "2Gi"
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 5
}

# Scheduling Configuration
variable "metrics_aggregation_schedule" {
  description = "Cron schedule for metrics aggregation"
  type        = string
  default     = "*/5 * * * *"  # Every 5 minutes
}

variable "alert_processing_schedule" {
  description = "Cron schedule for alert processing"
  type        = string
  default     = "*/2 * * * *"  # Every 2 minutes
}

# Monitoring Configuration
variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

variable "alert_thresholds" {
  description = "Alert threshold configurations"
  type = object({
    response_time_ms = number
    error_rate       = number
    cpu_utilization  = number
    memory_usage     = number
  })
  default = {
    response_time_ms = 5000
    error_rate       = 0.05
    cpu_utilization  = 0.8
    memory_usage     = 0.8
  }
}

# Budget Configuration
variable "enable_budget_alerts" {
  description = "Enable budget alerts"
  type        = bool
  default     = true
}

variable "billing_account_id" {
  description = "Billing account ID for budget alerts"
  type        = string
  default     = ""
}

variable "monthly_budget" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 200
}

# Security Configuration
variable "allowed_ingress" {
  description = "Allowed ingress configuration for Cloud Run"
  type        = string
  default     = "INGRESS_TRAFFIC_ALL"
}

variable "vpc_connector" {
  description = "VPC connector for private networking"
  type        = string
  default     = ""
}

# Performance Configuration
variable "concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 1000
}

variable "execution_environment" {
  description = "Execution environment (EXECUTION_ENVIRONMENT_GEN1 or EXECUTION_ENVIRONMENT_GEN2)"
  type        = string
  default     = "EXECUTION_ENVIRONMENT_GEN2"
}

# Dashboard Configuration
variable "dashboard_refresh_interval" {
  description = "Dashboard refresh interval in seconds"
  type        = number
  default     = 30
}

variable "data_retention_days" {
  description = "Data retention period in days"
  type        = number
  default     = 90
}

variable "max_dashboard_widgets" {
  description = "Maximum number of widgets per dashboard"
  type        = number
  default     = 50
}

# Monitoring Data Sources
variable "enabled_data_sources" {
  description = "List of enabled monitoring data sources"
  type        = list(string)
  default     = [
    "cloud_run_metrics",
    "bigquery_metrics", 
    "cloud_scheduler_metrics",
    "custom_trading_metrics"
  ]
}

# Alert Configuration
variable "alert_channels" {
  description = "Alert notification channels configuration"
  type = object({
    email    = list(string)
    slack    = list(string)
    webhook  = list(string)
  })
  default = {
    email   = []
    slack   = []
    webhook = []
  }
}

variable "alert_severity_levels" {
  description = "Alert severity level thresholds"
  type = object({
    critical = number
    warning  = number
    info     = number
  })
  default = {
    critical = 0.95
    warning  = 0.8
    info     = 0.6
  }
}
