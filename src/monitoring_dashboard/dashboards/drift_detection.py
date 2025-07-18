"""
Model and Data Drift Detection System for AI Trading Machine

Implements automated monitoring for:
- Data drift detection using statistical tests
- Model performance drift monitoring
- Feature distribution changes
- Regime shift detection
"""

import json
import logging
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    Comprehensive drift detection system for monitoring data and model drift
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize drift detector with configuration"""
        self.config = self._load_config(config_path)
        self.drift_history = []
        self.reference_data = {}
        self.performance_baseline = {}

    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load drift detection configuration"""
        default_config = {
            "data_drift": {
                "statistical_tests": ["ks_test", "chi2_test", "psi"],
                "significance_level": 0.05,
                "psi_threshold": 0.2,
                "feature_importance_threshold": 0.1,
            },
            "model_drift": {
                "performance_threshold": 0.15,  # 15% degradation threshold
                "window_size": 30,  # days
                "metrics": ["mse", "mae", "accuracy"],
            },
            "regime_detection": {
                "volatility_threshold": 2.0,  # 2x normal volatility
                "correlation_threshold": 0.3,  # 30% correlation change
                "lookback_period": 90,  # days
            },
            "alerts": {
                "critical_threshold": 0.8,
                "warning_threshold": 0.5,
                "escalation_delay": 3600,  # 1 hour
            },
        }

        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    def set_reference_data(self, data: pd.DataFrame, label: str = "baseline"):
        """Set reference data for drift detection"""
        try:
            # Store reference statistics
            self.reference_data[label] = {
                "timestamp": datetime.now(),
                "statistics": self._calculate_statistics(data),
                "feature_distributions": self._calculate_distributions(data),
                "data_shape": data.shape,
                "missing_rates": data.isnull().mean().to_dict(),
            }

            logger.info("Reference data set for '{label}': {data.shape}")
            return True

        except Exception as e:
            logger.error("Error setting reference data: {e}")
            return False

    def detect_data_drift(
        self, current_data: pd.DataFrame, reference_label: str = "baseline"
    ) -> dict:
        """
        Detect data drift using statistical tests
        """
        try:
            if reference_label not in self.reference_data:
                raise ValueError("Reference data '{reference_label}' not found")

            reference = self.reference_data[reference_label]
            drift_results = {
                "timestamp": datetime.now(),
                "reference_label": reference_label,
                "tests_performed": [],
                "drift_detected": False,
                "severity": "low",
                "feature_drifts": {},
                "overall_score": 0.0,
                "recommendations": [],
            }

            # Kolmogorov-Smirnov test for numerical features
            numerical_features = current_data.select_dtypes(include=[np.number]).columns
            for feature in numerical_features:
                if feature in reference["feature_distributions"]:
                    drift_score = self._ks_test_drift(
                        current_data[feature].dropna(),
                        reference["feature_distributions"][feature]["values"],
                    )
                    drift_results["feature_drifts"][feature] = drift_score

            # Population Stability Index (PSI)
            psi_scores = self._calculate_psi(current_data, reference)
            drift_results["psi_scores"] = psi_scores

            # Missing value drift
            current_missing = current_data.isnull().mean()
            missing_drift = self._detect_missing_drift(
                current_missing, reference["missing_rates"]
            )
            drift_results["missing_drift"] = missing_drift

            # Calculate overall drift score
            drift_results["overall_score"] = self._calculate_overall_drift_score(
                drift_results["feature_drifts"], psi_scores, missing_drift
            )

            # Determine severity and recommendations
            drift_results["severity"] = self._determine_severity(
                drift_results["overall_score"]
            )
            drift_results["drift_detected"] = (
                drift_results["overall_score"]
                > self.config["alerts"]["warning_threshold"]
            )
            drift_results["recommendations"] = self._generate_drift_recommendations(
                drift_results
            )

            # Store in history
            self.drift_history.append(drift_results)

            logger.info(
                "Data drift detection completed. "
                "Score: {drift_results['overall_score']:.3f}, "
                "Severity: {drift_results['severity']}"
            )

            return drift_results

        except Exception as e:
            logger.error("Error in data drift detection: {e}")
            return {"error": str(e), "timestamp": datetime.now()}

    def detect_model_drift(
        self, predictions: np.ndarray, actuals: np.ndarray, model_name: str = "default"
    ) -> dict:
        """
        Detect model performance drift
        """
        try:
            # Calculate current performance metrics
            current_metrics = {
                "mse": mean_squared_error(actuals, predictions),
                "mae": mean_absolute_error(actuals, predictions),
                "correlation": np.corrcoef(actuals, predictions)[0, 1],
            }

            # Initialize baseline if not exists
            if model_name not in self.performance_baseline:
                self.performance_baseline[model_name] = {
                    "baseline_metrics": current_metrics,
                    "history": [current_metrics],
                    "timestamp": datetime.now(),
                }
                return {
                    "model_name": model_name,
                    "status": "baseline_set",
                    "metrics": current_metrics,
                }

            baseline = self.performance_baseline[model_name]["baseline_metrics"]

            # Calculate performance drift
            drift_results = {
                "timestamp": datetime.now(),
                "model_name": model_name,
                "current_metrics": current_metrics,
                "baseline_metrics": baseline,
                "drift_scores": {},
                "drift_detected": False,
                "severity": "low",
                "recommendations": [],
            }

            # Calculate drift for each metric
            for metric in current_metrics:
                if metric in baseline:
                    drift_pct = abs(
                        (current_metrics[metric] - baseline[metric]) / baseline[metric]
                    )
                    drift_results["drift_scores"][metric] = drift_pct

            # Determine overall drift
            max_drift = max(drift_results["drift_scores"].values())
            drift_results["max_drift"] = max_drift
            drift_results["drift_detected"] = (
                max_drift > self.config["model_drift"]["performance_threshold"]
            )

            # Determine severity
            if max_drift > 0.3:
                drift_results["severity"] = "critical"
            elif max_drift > 0.2:
                drift_results["severity"] = "high"
            elif max_drift > 0.1:
                drift_results["severity"] = "medium"

            # Generate recommendations
            drift_results["recommendations"] = self._generate_model_recommendations(
                drift_results
            )

            # Update history
            self.performance_baseline[model_name]["history"].append(current_metrics)

            logger.info(
                "Model drift detection completed for '{model_name}'. "
                "Max drift: {max_drift:.3f}, "
                "Severity: {drift_results['severity']}"
            )

            return drift_results

        except Exception as e:
            logger.error("Error in model drift detection: {e}")
            return {"error": str(e), "timestamp": datetime.now()}

    def detect_regime_shift(self, market_data: pd.DataFrame) -> dict:
        """
        Detect market regime shifts using volatility and correlation analysis
        """
        try:
            # Calculate rolling volatility
            returns = market_data.pct_change().dropna()
            volatility = returns.rolling(window=20).std()

            # Calculate correlation matrix changes
            correlation_stability = self._analyze_correlation_stability(returns)

            # Detect volatility regime shifts
            vol_regime = self._detect_volatility_regime(volatility)

            regime_results = {
                "timestamp": datetime.now(),
                "volatility_regime": vol_regime,
                "correlation_stability": correlation_stability,
                "regime_shift_detected": False,
                "severity": "low",
                "recommendations": [],
            }

            # Determine if regime shift occurred
            high_vol_regime = vol_regime["current_regime"] == "high_volatility"
            unstable_correlations = correlation_stability["stability_score"] < 0.7

            regime_results["regime_shift_detected"] = (
                high_vol_regime or unstable_correlations
            )

            if regime_results["regime_shift_detected"]:
                if high_vol_regime and unstable_correlations:
                    regime_results["severity"] = "critical"
                elif high_vol_regime or correlation_stability["stability_score"] < 0.5:
                    regime_results["severity"] = "high"
                else:
                    regime_results["severity"] = "medium"

            # Generate recommendations
            regime_results["recommendations"] = self._generate_regime_recommendations(
                regime_results
            )

            logger.info(
                "Regime shift detection completed. "
                "Shift detected: {regime_results['regime_shift_detected']}, "
                "Severity: {regime_results['severity']}"
            )

            return regime_results

        except Exception as e:
            logger.error("Error in regime shift detection: {e}")
            return {"error": str(e), "timestamp": datetime.now()}

    def generate_drift_report(self, days_back: int = 30) -> dict:
        """Generate comprehensive drift report"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_drifts = [
                d
                for d in self.drift_history
                if d.get("timestamp", datetime.min) > cutoff_date
            ]

            report = {
                "timestamp": datetime.now(),
                "period_days": days_back,
                "total_checks": len(recent_drifts),
                "drift_events": len(
                    [d for d in recent_drifts if d.get("drift_detected")]
                ),
                "severity_breakdown": {},
                "trending_features": [],
                "recommendations": [],
                "action_items": [],
            }

            # Severity breakdown
            for severity in ["critical", "high", "medium", "low"]:
                report["severity_breakdown"][severity] = len(
                    [d for d in recent_drifts if d.get("severity") == severity]
                )

            # Feature trend analysis
            if recent_drifts:
                report["trending_features"] = self._analyze_feature_trends(
                    recent_drifts
                )

            # Generate action items
            critical_drifts = [
                d for d in recent_drifts if d.get("severity") == "critical"
            ]
            if critical_drifts:
                report["action_items"].extend(
                    [
                        "Immediate investigation required for critical drift events",
                        "Consider model retraining or strategy adjustment",
                        "Review data pipeline for systematic issues",
                    ]
                )

            logger.info(
                "Drift report generated: {report['drift_events']} "
                "drift events in {days_back} days"
            )

            return report

        except Exception as e:
            logger.error("Error generating drift report: {e}")
            return {"error": str(e), "timestamp": datetime.now()}

    def _calculate_statistics(self, data: pd.DataFrame) -> dict:
        """Calculate basic statistics for reference data"""
        stats_dict = {}
        for column in data.select_dtypes(include=[np.number]).columns:
            stats_dict[column] = {
                "mean": data[column].mean(),
                "std": data[column].std(),
                "min": data[column].min(),
                "max": data[column].max(),
                "quantiles": data[column].quantile([0.25, 0.5, 0.75]).to_dict(),
            }
        return stats_dict

    def _calculate_distributions(self, data: pd.DataFrame) -> dict:
        """Calculate feature distributions for drift detection"""
        distributions = {}
        for column in data.select_dtypes(include=[np.number]).columns:
            values = data[column].dropna()
            distributions[column] = {
                "values": values.tolist(),
                "histogram": np.histogram(values, bins=20)[0].tolist(),
                "bin_edges": np.histogram(values, bins=20)[1].tolist(),
            }
        return distributions

    def _ks_test_drift(
        self, current_data: pd.Series, reference_data: list[float]
    ) -> dict:
        """Perform Kolmogorov-Smirnov test for drift detection"""
        try:
            statistic, p_value = stats.ks_2samp(current_data, reference_data)
            return {
                "test": "ks_test",
                "statistic": statistic,
                "p_value": p_value,
                "drift_detected": p_value
                < self.config["data_drift"]["significance_level"],
                "severity": (
                    "high" if p_value < 0.01 else "medium" if p_value < 0.05 else "low"
                ),
            }
        except Exception as e:
            return {"test": "ks_test", "error": str(e)}

    def _calculate_psi(self, current_data: pd.DataFrame, reference: dict) -> dict:
        """Calculate Population Stability Index"""
        psi_scores = {}

        for feature in current_data.select_dtypes(include=[np.number]).columns:
            if feature in reference["feature_distributions"]:
                try:
                    # Get reference histogram
                    ref_hist = np.array(
                        reference["feature_distributions"][feature]["histogram"]
                    )
                    ref_edges = np.array(
                        reference["feature_distributions"][feature]["bin_edges"]
                    )

                    # Calculate current histogram with same bins
                    current_hist, _ = np.histogram(
                        current_data[feature].dropna(), bins=ref_edges
                    )

                    # Normalize to get proportions
                    ref_prop = ref_hist / ref_hist.sum()
                    current_prop = current_hist / current_hist.sum()

                    # Calculate PSI
                    psi = np.sum(
                        (current_prop - ref_prop)
                        * np.log(current_prop / (ref_prop + 1e-10))
                    )

                    psi_scores[feature] = {
                        "psi_score": psi,
                        "drift_detected": psi
                        > self.config["data_drift"]["psi_threshold"],
                        "severity": (
                            "high" if psi > 0.25 else "medium" if psi > 0.1 else "low"
                        ),
                    }

                except Exception as e:
                    psi_scores[feature] = {"error": str(e)}

        return psi_scores

    def _detect_missing_drift(
        self, current_missing: pd.Series, reference_missing: dict
    ) -> dict:
        """Detect drift in missing value patterns"""
        missing_drift = {}

        for feature, current_rate in current_missing.items():
            if feature in reference_missing:
                ref_rate = reference_missing[feature]
                diff = abs(current_rate - ref_rate)

                missing_drift[feature] = {
                    "current_missing_rate": current_rate,
                    "reference_missing_rate": ref_rate,
                    "difference": diff,
                    "drift_detected": diff > 0.1,  # 10% threshold
                    "severity": (
                        "high" if diff > 0.2 else "medium" if diff > 0.1 else "low"
                    ),
                }

        return missing_drift

    def _calculate_overall_drift_score(
        self, feature_drifts: dict, psi_scores: dict, missing_drift: dict
    ) -> float:
        """Calculate overall drift score"""
        scores = []

        # Feature drift scores
        for feature, drift_info in feature_drifts.items():
            if "statistic" in drift_info:
                scores.append(drift_info["statistic"])

        # PSI scores
        for feature, psi_info in psi_scores.items():
            if "psi_score" in psi_info:
                scores.append(min(psi_info["psi_score"], 1.0))  # Cap at 1.0

        # Missing drift scores
        for feature, missing_info in missing_drift.items():
            if "difference" in missing_info:
                scores.append(missing_info["difference"])

        return np.mean(scores) if scores else 0.0

    def _determine_severity(self, drift_score: float) -> str:
        """Determine drift severity based on score"""
        if drift_score > self.config["alerts"]["critical_threshold"]:
            return "critical"
        elif drift_score > self.config["alerts"]["warning_threshold"]:
            return "high"
        elif drift_score > 0.3:
            return "medium"
        else:
            return "low"

    def _generate_drift_recommendations(self, drift_results: dict) -> list[str]:
        """Generate actionable recommendations for drift"""
        recommendations = []

        if drift_results["severity"] == "critical":
            recommendations.extend(
                [
                    "Immediate action required - critical data drift detected",
                    "Stop trading and investigate data pipeline",
                    "Consider emergency model retraining",
                ]
            )
        elif drift_results["severity"] == "high":
            recommendations.extend(
                [
                    "Investigate data source changes",
                    "Consider model recalibration",
                    "Increase monitoring frequency",
                ]
            )
        elif drift_results["severity"] == "medium":
            recommendations.extend(
                [
                    "Monitor closely for trend continuation",
                    "Review feature engineering pipeline",
                    "Plan model update within 1-2 weeks",
                ]
            )

        return recommendations

    def _generate_model_recommendations(self, drift_results: dict) -> list[str]:
        """Generate recommendations for model drift"""
        recommendations = []

        if drift_results["severity"] == "critical":
            recommendations.extend(
                [
                    "Immediate model intervention required",
                    "Consider switching to backup model",
                    "Emergency retraining recommended",
                ]
            )
        elif drift_results["severity"] == "high":
            recommendations.extend(
                [
                    "Schedule model retraining within 24 hours",
                    "Increase validation frequency",
                    "Review recent data quality",
                ]
            )

        return recommendations

    def _detect_volatility_regime(self, volatility: pd.Series) -> dict:
        """Detect volatility regime changes"""
        try:
            recent_vol = volatility.tail(20).mean()
            historical_vol = volatility.quantile(0.8)

            if recent_vol > historical_vol * 1.5:
                regime = "high_volatility"
            elif recent_vol < historical_vol * 0.7:
                regime = "low_volatility"
            else:
                regime = "normal_volatility"

            return {
                "current_regime": regime,
                "recent_volatility": recent_vol,
                "historical_threshold": historical_vol,
                "volatility_ratio": recent_vol / historical_vol,
            }

        except Exception as e:
            return {"error": str(e)}

    def _analyze_correlation_stability(self, returns: pd.DataFrame) -> dict:
        """Analyze correlation matrix stability"""
        try:
            # Calculate rolling correlations
            window = 30
            recent_corr = returns.tail(window).corr()
            historical_corr = returns.head(-window).corr()

            # Calculate correlation stability
            corr_diff = np.abs(recent_corr - historical_corr).fillna(0)
            stability_score = 1 - corr_diff.mean().mean()

            return {
                "stability_score": stability_score,
                "max_correlation_change": corr_diff.max().max(),
                "unstable_pairs": int((corr_diff > 0.3).sum().sum()),
            }

        except Exception as e:
            return {"error": str(e)}

    def _generate_regime_recommendations(self, regime_results: dict) -> list[str]:
        """Generate recommendations for regime shifts"""
        recommendations = []

        if regime_results["regime_shift_detected"]:
            if regime_results["severity"] == "critical":
                recommendations.extend(
                    [
                        "Major regime shift detected - reduce position sizes",
                        "Activate defensive strategies",
                        "Increase cash allocation",
                    ]
                )
            else:
                recommendations.extend(
                    [
                        "Monitor regime continuation",
                        "Consider strategy adjustments",
                        "Review risk parameters",
                    ]
                )

        return recommendations

    def _analyze_feature_trends(self, recent_drifts: list[dict]) -> list[dict]:
        """Analyze trending features across drift events"""
        feature_counts = {}

        for drift in recent_drifts:
            if "feature_drifts" in drift:
                for feature, drift_info in drift["feature_drifts"].items():
                    if drift_info.get("drift_detected"):
                        feature_counts[feature] = feature_counts.get(feature, 0) + 1

        # Sort by frequency
        trending = [
            {"feature": feature, "drift_count": count}
            for feature, count in sorted(
                feature_counts.items(), key=lambda x: x[1], reverse=True
            )
        ]

        return trending[:10]  # Top 10 trending features


# Factory function for easy initialization
def create_drift_detector(config_path: Optional[str] = None) -> DriftDetector:
    """Create and return a configured drift detector"""
    return DriftDetector(config_path)


if __name__ == "__main__":
    # Example usage
    detector = create_drift_detector()
    print("Drift detection system initialized successfully")
