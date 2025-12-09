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
import math
import json

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
import numpy as np
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
# CUSTOM JSON ENCODER
# ============================================================================

class NaNHandlingEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles NaN, Inf, and numpy types."""
    
    def encode(self, o):
        if isinstance(o, float):
            if math.isnan(o) or math.isinf(o):
                return 'null'
        return super().encode(o)
    
    def iterencode(self, o, _one_shot=False):
        """Override iterencode to handle NaN/Inf at all levels."""
        for chunk in super().iterencode(o, _one_shot):
            yield chunk
    
    def default(self, obj):
        """Handle objects that json doesn't know about."""
        # Handle numpy types
        if isinstance(obj, np.generic):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                val = float(obj)
                if math.isnan(val) or math.isinf(val):
                    return None
                return val
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, (np.datetime64, np.timedelta64)):
                return str(obj)
            elif isinstance(obj, (np.str_, np.unicode_)):
                return str(obj)
            else:
                return str(obj)
        
        # Handle pandas NA/NaT
        try:
            if pd.isna(obj):
                return None
        except (ValueError, TypeError):
            pass
        
        # Handle pandas Series
        if isinstance(obj, pd.Series):
            return obj.tolist()
        
        # Handle pandas Index
        if isinstance(obj, pd.Index):
            return obj.tolist()
        
        # Handle datetime
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        
        return super().default(obj)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def convert_to_json_serializable(obj):
    """Convert numpy and pandas types to JSON-serializable Python types.
    
    CRITICAL: Check collection types BEFORE calling pd.isna() to avoid
    "ambiguous truth value" errors on DataFrames and arrays.
    
    Handles:
    - numpy integer types (int8-int64, uint8-uint64)
    - numpy floating types (float16, float32, float64)
    - numpy bool
    - numpy string/unicode
    - numpy datetime64, timedelta64
    - NaN, Inf, -Inf (converted to null)
    - pandas NA/NaT values
    - nested structures (dicts, lists, tuples)
    """
    try:
        # IMPORTANT: Check collections FIRST (before pd.isna)
        # pd.isna on DataFrames/arrays throws "ambiguous truth value" error
        
        # Handle dictionaries recursively
        if isinstance(obj, dict):
            return {k: convert_to_json_serializable(v) for k, v in obj.items()}
        
        # Handle lists and tuples
        if isinstance(obj, (list, tuple)):
            return [convert_to_json_serializable(item) for item in obj]
        
        # Handle pandas Series/Index
        if isinstance(obj, (pd.Series, pd.Index)):
            return [convert_to_json_serializable(item) for item in obj.tolist()]
        
        # Handle DataFrames - convert to list of dicts with NaN handling
        if isinstance(obj, pd.DataFrame):
            return obj.where(pd.notna(obj), None).to_dict(orient='records')
        
        # Check for NaN/Inf (works for float and numpy.floating)
        if isinstance(obj, (float, np.floating)):
            val = float(obj)
            if math.isnan(val) or math.isinf(val):
                return None
            return val
        
        # Handle numpy generic types
        if isinstance(obj, np.generic):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                val = float(obj)
                if math.isnan(val) or math.isinf(val):
                    return None
                return val
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, (np.datetime64, np.timedelta64)):
                return str(obj)
            elif isinstance(obj, (np.str_, np.unicode_)):
                return str(obj)
            else:
                return str(obj)
        
        # NOW safe to check pd.isna (after collections checked)
        try:
            if pd.isna(obj):
                return None
        except (ValueError, TypeError):
            # If pd.isna fails, just return the object
            pass
        
        # Return as-is for standard Python types
        return obj
    
    except Exception as e:
        logger.warning(f"Could not convert type {type(obj)}: {e}", exc_info=True)
        return None


def safe_json_response(data):
    """Create JSON response with custom encoder that handles NaN."""
    try:
        # Use custom encoder
        json_str = json.dumps(data, cls=NaNHandlingEncoder, allow_nan=False)
        return JSONResponse(content=json.loads(json_str))
    except Exception as e:
        logger.error(f"Error encoding response: {e}", exc_info=True)
        # Fallback: convert and try again
        try:
            safe_data = convert_to_json_serializable(data)
            json_str = json.dumps(safe_data, cls=NaNHandlingEncoder, allow_nan=False)
            return JSONResponse(content=json.loads(json_str))
        except Exception as e2:
            logger.error(f"Fallback encoding also failed: {e2}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": "Could not serialize response data"}
            )


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
    """Load data from file.
    
    Loads data using DataLoader agent and returns metadata.
    Metadata is in result["metadata"] which contains rows, columns, etc.
    """
    try:
        logger.info(f"Loading data from: {request.file_path}")
        
        task = orchestrator.create_task("load_data", {"file_path": request.file_path})
        task_result = orchestrator.execute_task(task["id"])
        result = task_result.get("result", {})
        
        # Extract metadata from result
        # DataLoader returns: {"status": ..., "data": df, "metadata": {...}}
        metadata = result.get("metadata", {})
        
        logger.info(f"Successfully loaded data: {metadata.get('rows')} rows, {metadata.get('columns')} columns")
        
        # Convert metadata to JSON-serializable
        metadata = convert_to_json_serializable(metadata)
        
        response_data = {
            "status": "success",
            "file_path": metadata.get("file_path", ""),
            "rows": metadata.get("rows", 0),
            "columns": metadata.get("columns", 0),
            "columns_list": metadata.get("column_names", []),
        }
        
        return safe_json_response(response_data)

    except Exception as e:
        logger.error(f"Error loading data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# EXPLORATION ENDPOINTS
# ============================================================================

@app.post("/api/explore")
async def explore_data(request: ExploreDataRequest):
    """Explore data using Explorer agent with worker-based analysis.
    
    Returns comprehensive report with worker results and quality validation.
    """
    try:
        logger.info(f"Exploring data from key: {request.data_key}")
        
        data = orchestrator.get_cached_data(request.data_key)
        if data is None:
            raise HTTPException(status_code=404, detail="Data not found")
        
        # Use the Explorer agent with workers
        explorer = Explorer()
        explorer.set_data(data)
        
        # Get comprehensive report with all workers and validation
        report = explorer.get_summary_report()
        
        # Convert to JSON-serializable
        report = convert_to_json_serializable(report)
        
        logger.info(f"Data exploration complete")
        
        return safe_json_response(report)
    
    except Exception as e:
        logger.error(f"Error exploring data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# AGGREGATION ENDPOINTS
# ============================================================================

@app.post("/api/aggregate")
async def aggregate_data(request: AggregateRequest):
    """Aggregate data."""
    try:
        logger.info(f"Aggregating data by '{request.group_by}' on column '{request.agg_col}'")
        
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
        
        # Convert to JSON-serializable
        result = convert_to_json_serializable(result)
        
        logger.info(f"Aggregation complete")
        
        return safe_json_response(result)
    except Exception as e:
        logger.error(f"Error aggregating data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# VISUALIZATION ENDPOINTS
# ============================================================================

@app.post("/api/visualize")
async def visualize_data(request: VisualizationRequest):
    """Create visualization."""
    try:
        logger.info(f"Creating {request.chart_type} visualization")
        
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
        
        result = convert_to_json_serializable(result)
        
        logger.info(f"Visualization created")
        
        return safe_json_response(result)
    except Exception as e:
        logger.error(f"Error creating visualization: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@app.post("/api/predict")
async def predict(request: PredictionRequest):
    """Generate predictions."""
    try:
        logger.info(f"Generating {request.prediction_type} predictions")
        
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
        
        result = convert_to_json_serializable(result)
        
        logger.info(f"Predictions generated")
        
        return safe_json_response(result)
    except Exception as e:
        logger.error(f"Error generating predictions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ANOMALY DETECTION ENDPOINTS
# ============================================================================

@app.post("/api/detect-anomalies")
async def detect_anomalies(request: AnomalyRequest):
    """Detect anomalies."""
    try:
        logger.info(f"Detecting anomalies using {request.method} method")
        
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
        
        result = convert_to_json_serializable(result)
        
        logger.info(f"Anomaly detection complete")
        
        return safe_json_response(result)
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RECOMMENDATION ENDPOINTS
# ============================================================================

@app.post("/api/recommend")
async def get_recommendations(request: RecommendationRequest):
    """Get recommendations."""
    try:
        logger.info(f"Generating recommendations")
        
        task = orchestrator.create_task(
            "get_recommendations",
            {"data_key": request.data_key}
        )
        result = orchestrator.execute_task(task["id"])
        
        result = convert_to_json_serializable(result)
        
        logger.info(f"Recommendations generated")
        
        return safe_json_response(result)
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# REPORT ENDPOINTS
# ============================================================================

@app.post("/api/report")
async def generate_report(request: ReportRequest):
    """Generate report."""
    try:
        logger.info(f"Generating {request.report_type} report")
        
        task = orchestrator.create_task(
            "generate_report",
            {
                "data_key": request.data_key,
                "report_type": request.report_type,
            }
        )
        result = orchestrator.execute_task(task["id"])
        
        result = convert_to_json_serializable(result)
        
        logger.info(f"Report generated")
        
        return safe_json_response(result)
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# WORKFLOW ENDPOINTS
# ============================================================================

@app.post("/api/workflow")
async def execute_workflow(request: WorkflowRequest):
    """Execute a complete workflow."""
    try:
        logger.info(f"Executing workflow with {len(request.tasks)} tasks")
        
        workflow_result = orchestrator.execute_workflow(request.tasks)
        
        workflow_result = convert_to_json_serializable(workflow_result)
        
        logger.info(f"Workflow execution complete")
        
        return safe_json_response(workflow_result)
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/cache/{key}")
async def get_cached_data(key: str):
    """Get cached data."""
    try:
        logger.info(f"Retrieving cached data: {key}")
        
        data = orchestrator.get_cached_data(key)
        if data is None:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
        
        if isinstance(data, pd.DataFrame):
            # Convert DataFrame to safe dict with NaN handling
            head_data = data.head(10).where(pd.notna(data.head(10)), None).to_dict(orient="records")
            
            response_data = {
                "status": "success",
                "key": key,
                "type": "dataframe",
                "shape": list(data.shape),
                "columns": data.columns.tolist(),
                "head": head_data,
            }
            
            return safe_json_response(response_data)
        
        logger.info(f"Cached data retrieved successfully")
        
        return safe_json_response({"status": "success", "key": key, "data": str(data)})
    except Exception as e:
        logger.error(f"Error retrieving cached data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
