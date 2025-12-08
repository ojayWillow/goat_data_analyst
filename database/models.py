"""SQLAlchemy models for GOAT Data Analyst."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from database.connection import Base


class Dataset(Base):
    """Dataset model for storing uploaded data information."""
    
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # csv, xlsx, json, parquet
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    size_mb = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, nullable=True)  # Store column names, types, etc.


class Analysis(Base):
    """Analysis model for storing analysis results."""
    
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    analysis_type = Column(String(100), nullable=False)  # descriptive, predictive, anomaly, etc.
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    result_summary = Column(JSON, nullable=True)
    result_details = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)


class Visualization(Base):
    """Visualization model for storing generated charts."""
    
    __tablename__ = "visualizations"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    chart_type = Column(String(50), nullable=False)  # line, bar, scatter, heatmap, etc.
    chart_data = Column(JSON, nullable=False)
    chart_config = Column(JSON, nullable=True)  # plotly/matplotlib config
    created_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)


class Report(Base):
    """Report model for storing generated reports."""
    
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # summary, detailed, executive
    content = Column(Text, nullable=False)
    format = Column(String(20), default="pdf")  # pdf, html, markdown
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(100), nullable=True)


class Prediction(Base):
    """Prediction model for storing prediction results."""
    
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, nullable=False, index=True)
    model_type = Column(String(100), nullable=False)  # arima, prophet, xgboost, etc.
    prediction_data = Column(JSON, nullable=False)
    confidence_interval = Column(JSON, nullable=True)
    accuracy_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnomalyDetection(Base):
    """Anomaly detection model for storing anomaly results."""
    
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, nullable=False, index=True)
    detection_method = Column(String(100), nullable=False)  # isolation_forest, z_score, etc.
    anomaly_data = Column(JSON, nullable=False)
    anomaly_count = Column(Integer, default=0)
    severity_scores = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Insight(Base):
    """Insight model for storing discovered insights and recommendations."""
    
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, nullable=False, index=True)
    insight_type = Column(String(50), nullable=False)  # correlation, trend, anomaly_explanation, etc.
    description = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    actionable = Column(Boolean, default=True)
    recommendations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
