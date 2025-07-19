# Monitoring Dashboard Terraform Infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    bucket = "ai-trading-terraform-state"
    prefix = "monitoring-dashboard"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "monitoring_dashboard" {
  location      = var.region
  repository_id = "monitoring-dashboard"
  description   = "Monitoring Dashboard Docker repository"
  format        = "DOCKER"

  labels = {
    component   = "monitoring-dashboard"
    environment = var.environment
    managed-by  = "terraform"
  }
}

# Service Account for Monitoring Dashboard
resource "google_service_account" "monitoring_dashboard" {
  account_id   = "monitoring-dashboard-sa"
  display_name = "Monitoring Dashboard Service Account"
  description  = "Service account for Monitoring Dashboard"
}

# IAM bindings for service account
resource "google_project_iam_member" "monitoring_dashboard_bigquery_user" {
  project = var.project_id
  role    = "roles/bigquery.user"
  member  = "serviceAccount:${google_service_account.monitoring_dashboard.email}"
}

resource "google_project_iam_member" "monitoring_dashboard_monitoring_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.monitoring_dashboard.email}"
}

resource "google_project_iam_member" "monitoring_dashboard_logging_viewer" {
  project = var.project_id
  role    = "roles/logging.viewer"
  member  = "serviceAccount:${google_service_account.monitoring_dashboard.email}"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "monitoring_dashboard" {
  name     = "monitoring-dashboard"
  location = var.region
  
  deletion_protection = false

  template {
    service_account = google_service_account.monitoring_dashboard.email
    
    timeout = "300s"
    
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/monitoring-dashboard/monitoring-dashboard:latest"
      
      ports {
        container_port = 8080
      }
      
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      
      env {
        name  = "REGION"
        value = var.region
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }
      
      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 30
        timeout_seconds       = 10
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 60
        timeout_seconds       = 10
        period_seconds        = 30
        failure_threshold     = 3
      }
    }
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    
    labels = {
      component   = "monitoring-dashboard"
      environment = var.environment
      managed-by  = "terraform"
    }
  }
  
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [google_artifact_registry_repository.monitoring_dashboard]
}

# IAM policy for Cloud Run service (allow authenticated users)
resource "google_cloud_run_service_iam_member" "monitoring_dashboard_invoker" {
  service  = google_cloud_run_v2_service.monitoring_dashboard.name
  location = google_cloud_run_v2_service.monitoring_dashboard.location
  role     = "roles/run.invoker"
  member   = "allAuthenticatedUsers"
}

# BigQuery dataset for monitoring data
resource "google_bigquery_dataset" "monitoring_data" {
  dataset_id    = "monitoring_data"
  friendly_name = "Monitoring Data"
  description   = "Dataset for storing monitoring metrics and dashboard data"
  location      = var.bigquery_location

  labels = {
    component   = "monitoring-dashboard"
    environment = var.environment
    managed-by  = "terraform"
  }

  delete_contents_on_destroy = false

  access {
    role          = "OWNER"
    user_by_email = google_service_account.monitoring_dashboard.email
  }
}

# Cloud Scheduler job for metrics aggregation
resource "google_cloud_scheduler_job" "metrics_aggregation" {
  name        = "metrics-aggregation-job"
  description = "Aggregate metrics for dashboard"
  schedule    = var.metrics_aggregation_schedule
  time_zone   = var.timezone
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.monitoring_dashboard.uri}/aggregate-metrics"
    
    oidc_token {
      service_account_email = google_service_account.monitoring_dashboard.email
    }
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      action = "aggregate_all_metrics"
    }))
  }
}

# Cloud Scheduler job for alert processing
resource "google_cloud_scheduler_job" "alert_processing" {
  name        = "alert-processing-job"
  description = "Process and send alerts"
  schedule    = var.alert_processing_schedule
  time_zone   = var.timezone
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.monitoring_dashboard.uri}/process-alerts"
    
    oidc_token {
      service_account_email = google_service_account.monitoring_dashboard.email
    }
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      action = "process_pending_alerts"
    }))
  }
}

# Monitoring alert policy for dashboard health
resource "google_monitoring_alert_policy" "dashboard_health" {
  display_name = "Monitoring Dashboard Health"
  combiner     = "OR"
  
  conditions {
    display_name = "Dashboard Response Time"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"monitoring-dashboard\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 5000  # 5 seconds
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields = ["resource.labels.service_name"]
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  alert_strategy {
    auto_close = "86400s"
  }
}

# Budget alert for monitoring dashboard costs
resource "google_billing_budget" "monitoring_dashboard_budget" {
  count = var.enable_budget_alerts ? 1 : 0
  
  billing_account = var.billing_account_id
  display_name    = "Monitoring Dashboard Budget"

  budget_filter {
    projects = ["projects/${var.project_id}"]
    labels = {
      component = "monitoring-dashboard"
    }
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget)
    }
  }

  threshold_rules {
    threshold_percent = 0.8
    spend_basis      = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis      = "CURRENT_SPEND"
  }
}
