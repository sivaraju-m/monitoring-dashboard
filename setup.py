from setuptools import setup, find_packages

setup(
    name="monitoring-dashboard",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.22.0",
        "dash>=2.0.0",
        "plotly>=5.0.0",
        "flask>=2.0.0",
        "shared-services>=0.1.0",
        "pyyaml>=6.0",
        "google-cloud-monitoring>=2.0.0",
        "google-cloud-monitoring-dashboards>=2.0.0",
        "google-cloud-pubsub>=2.0.0",
        "google-cloud-storage>=2.0.0",
    ],
    author="AI Trading Machine Team",
    author_email="team@aitradingmachine.com",
    description="Monitoring dashboard for AI Trading Machine",
    python_requires=">=3.8",
)
