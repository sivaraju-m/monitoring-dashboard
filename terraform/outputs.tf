# Monitoring Dashboard Terraform Outputs

output "service_account_email" {
  description = "Email of the Monitoring Dashboard service account"
  value       = google_service_account.monitoring_dashboard.email
}

output "cloud_run_service_url" {
  description = "URL of the Monitoring Dashboard Cloud Run service"
  value       = google_cloud_run_v2_service.monitoring_dashboard.uri
}

output "cloud_run_service_name" {
  description = "Name of the Monitoring Dashboard Cloud Run service"
  value       = google_cloud_run_v2_service.monitoring_dashboard.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository for Docker images"
  value       = google_artifact_registry_repository.monitoring_dashboard.name
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.monitoring_dashboard.repository_id}"
}

output "bigquery_dataset_id" {
  description = "BigQuery dataset ID for monitoring data"
  value       = google_bigquery_dataset.monitoring_data.dataset_id
}

output "bigquery_dataset_location" {
  description = "BigQuery dataset location"
  value       = google_bigquery_dataset.monitoring_data.location
}

output "scheduler_job_names" {
  description = "Names of Cloud Scheduler jobs"
  value = [
    google_cloud_scheduler_job.metrics_aggregation.name,
    google_cloud_scheduler_job.alert_processing.name
  ]
}

output "monitoring_alert_policy_name" {
  description = "Name of the monitoring alert policy"
  value       = google_monitoring_alert_policy.dashboard_health.name
}

output "budget_name" {
  description = "Name of the budget alert (if enabled)"
  value       = var.enable_budget_alerts ? google_billing_budget.monitoring_dashboard_budget[0].display_name : null
}

# Configuration outputs for other services
output "monitoring_dashboard_config" {
  description = "Monitoring Dashboard configuration for other services"
  value = {
    service_url           = google_cloud_run_v2_service.monitoring_dashboard.uri
    service_account_email = google_service_account.monitoring_dashboard.email
    dataset_id           = google_bigquery_dataset.monitoring_data.dataset_id
    metrics_aggregation_schedule = var.metrics_aggregation_schedule
    alert_processing_schedule = var.alert_processing_schedule
  }
  sensitive = false
}

# Deployment information
output "deployment_info" {
  description = "Deployment information and next steps"
  value = {
    docker_image_url = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.monitoring_dashboard.repository_id}/monitoring-dashboard:latest"
    health_check_url = "${google_cloud_run_v2_service.monitoring_dashboard.uri}/health"
    dashboard_url = "${google_cloud_run_v2_service.monitoring_dashboard.uri}/"
    metrics_endpoint = "${google_cloud_run_v2_service.monitoring_dashboard.uri}/aggregate-metrics"
    alerts_endpoint = "${google_cloud_run_v2_service.monitoring_dashboard.uri}/process-alerts"
  }
}
