"""FastAPI server for GOAT Data Analyst.

Provides REST API endpoints for all agents.

Usage:
    From project root:
    python -m api.main
    
    Or:
    uvicorn api.main:app --reload --app-dir . 
    
API will be available at: http://localhost:8000
API docs: http://localhost:8000/docs
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pandas as pd
import io
import json
from datetime import datetime

from agents.orchestrator import Orchestrator
from agents.data_loader import DataLoader
from agents.explorer import Explorer
from agents.aggregator import Aggregator
from agents.visualizer import Visualizer
from agents.predictor import Predictor
from agents.anomaly_detector import AnomalyDetector
from agents.recommender import Recommender
from agents.reporter import Reporter
from core.logger import get_logger

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GOAT Data Analyst API",
    description="REST API for intelligent data analysis with 9 specialized agents",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Orchestrator and agents
logger.info("Initializing Orchestrator...")
orchestrator = Orchestrator()

agents = [
    ("data_loader", DataLoader()),
    ("explorer", Explorer()),
    ("aggregator", Aggregator()),
    ("visualizer", Visualizer()),
    ("predictor", Predictor()),
    ("anomaly_detector", AnomalyDetector()),
    ("recommender", Recommender()),
    ("reporter", Reporter()),
]

for agent_name, agent_instance in agents:
    orchestrator.register_agent(agent_name, agent_instance)

logger.info("FastAPI server initialized with all agents")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LoadDataRequest(BaseModel):
    """Request model for loading data."""
    file_path: str


class ExploreDataRequest(BaseModel):
    """Request model for exploring data."""
    data_key: str = "loaded_data"


class AggregateRequest(BaseModel):
    """Request model for aggregation."""
    data_key: str = "loaded_data"
    group_by: str
    agg_col: str
    agg_func: str = "sum"


class VisualizationRequest(BaseModel):
    """Request model for visualization."""
    data_key: str = "loaded_data"
    chart_type: str = "histogram"
    column: Optional[str] = None
    x_col: Optional[str] = None
    y_col: Optional[str] = None
    bins: int = 30


class PredictionRequest(BaseModel):
    """Request model for predictions."""
    data_key: str = "loaded_data"
    prediction_type: str = "trend"
    column: Optional[str] = None
    x_col: Optional[str] = None
    y_col: Optional[str] = None
    periods: int = 10


class AnomalyRequest(BaseModel):
    """Request model for anomaly detection."""
    data_key: str = "loaded_data"
    method: str = "iqr"
    column: Optional[str] = None
    multiplier: float = 1.5
    threshold: float = 3.0


class RecommendationRequest(BaseModel):
    """Request model for recommendations."""
    data_key: str = "loaded_data"


class ReportRequest(BaseModel):
    """Request model for report generation."""
    data_key: str = "loaded_data"
    report_type: str = "executive_summary"


class WorkflowRequest(BaseModel):
    """Request model for workflow execution."""
    tasks: List[Dict[str, Any]]


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "GOAT Data Analyst API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "agents": orchestrator.list_agents(),
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agents_registered": len(orchestrator.list_agents()),
    }


@app.get("/status")
async def status():
    """Get orchestrator status."""
    return orchestrator.get_workflow_status()


@app.get("/agents")
async def list_agents():
    """List all available agents."""
    return {
        "agents": orchestrator.list_agents(),
        "count": len(orchestrator.list_agents()),
    }


# ============================================================================
# DATA LOADING ENDPOINTS
# ============================================================================

@app.post("/api/load")
async def load_data(request: LoadDataRequest):
    """Load data from file."""
    try:
        task = orchestrator.create_task("load_data", {"file_path": request.file_path})
        result = orchestrator.execute_task(task["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/upload")
async def upload_data(file: UploadFile = File(...)):
    """Upload and load data file."""
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Cache the data
        orchestrator.cache_data("uploaded_data", df)
        
        return {
            "status": "success",
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "shape": df.shape,
            "columns_list": df.columns.tolist(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# EXPLORATION ENDPOINTS
# ============================================================================

@app.post("/api/explore")
async def explore_data(request: ExploreDataRequest):
    """Explore data."""
    try:
        task = orchestrator.create_task("explore_data", {"data_key": request.data_key})
        result = orchestrator.execute_task(task["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# AGGREGATION ENDPOINTS
# ============================================================================

@app.post("/api/aggregate")
async def aggregate_data(request: AggregateRequest):
    """Aggregate data."""
    try:
        task = orchestrator.create_task(
            "aggregate_data",
            {
                "data_key": request.data_key,
                "group_by": request.group_by,
                "agg_col": request.agg_col,
                "agg_func": request.agg_func,
            }
        )
        result = orchestrator.execute_task(task["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# VISUALIZATION ENDPOINTS
# ============================================================================

@app.post("/api/visualize")
async def visualize_data(request: VisualizationRequest):
    """Create visualization."""
    try:
        task = orchestrator.create_task(
            "visualize_data",
            {
                "data_key": request.data_key,
                "chart_type": request.chart_type,
                "column": request.column,
                "x_col": request.x_col,
                "y_col": request.y_col,
                "bins": request.bins,
            }
        )
        result = orchestrator.execute_task(task["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@app.post("/api/predict")
async def predict(request: PredictionRequest):
    """Generate predictions."""
    try:
        task = orchestrator.create_task(
            "predict",
            {
                "data_key": request.data_key,
                "prediction_type": request.prediction_type,
                "column": request.column,
                "x_col": request.x_col,
                "y_col": request.y_col,
                "periods": request.periods,
            }
        )
        result = orchestrator.execute_task(task["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ANOMALY DETECTION ENDPOINTS
# ============================================================================

@app.post("/api/detect-anomalies")
async def detect_anomalies(request: AnomalyRequest):
    """Detect anomalies."""
    try:
        task = orchestrator.create_task(
            "detect_anomalies",
            {
                "data_key": request.data_key,
                "method": request.method,
                "column": request.column,
                "multiplier": request.multiplier,
                "threshold": request.threshold,
            }
        )
        result = orchestrator.execute_task(task["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RECOMMENDATION ENDPOINTS
# ============================================================================

@app.post("/api/recommend")
async def get_recommendations(request: RecommendationRequest):
    """Get recommendations."""
    try:
        task = orchestrator.create_task(
            "get_recommendations",
            {"data_key": request.data_key}
        )
        result = orchestrator.execute_task(task["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# REPORT ENDPOINTS
# ============================================================================

@app.post("/api/report")
async def generate_report(request: ReportRequest):
    """Generate report."""
    try:
        task = orchestrator.create_task(
            "generate_report",
            {
                "data_key": request.data_key,
                "report_type": request.report_type,
            }
        )
        result = orchestrator.execute_task(task["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# WORKFLOW ENDPOINTS
# ============================================================================

@app.post("/api/workflow")
async def execute_workflow(request: WorkflowRequest):
    """Execute a complete workflow."""
    try:
        workflow_result = orchestrator.execute_workflow(request.tasks)
        return workflow_result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/cache/{key}")
async def get_cached_data(key: str):
    """Get cached data."""
    try:
        data = orchestrator.get_cached_data(key)
        if data is None:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
        
        if isinstance(data, pd.DataFrame):
            return {
                "status": "success",
                "key": key,
                "type": "dataframe",
                "shape": data.shape,
                "columns": data.columns.tolist(),
                "head": data.head(10).to_dict(orient="records"),
            }
        return {"status": "success", "key": key, "data": str(data)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
