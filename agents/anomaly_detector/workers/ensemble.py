"""Ensemble - Ensemble anomaly detection using voting.

This worker combines multiple anomaly detection algorithms using a voting mechanism.
Each algorithm provides its prediction, and an anomaly is flagged if it receives votes
from a sufficient number of algorithms.

All methods follow A+ quality standards with comprehensive error handling and quality tracking.
"""

import pandas as pd
import numpy as np
from typing import Any, Optional, List, Dict

from .lof import LOF
from .ocsvm import OneClassSVM
from .isolation_forest import IsolationForest as IFWorker
from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

# ===== CONSTANTS =====
DEFAULT_THRESHOLD: float = 0.5  # Voting threshold (fraction of algos that must agree)
MIN_SUCCESSFUL_ALGOS: int = 1   # Minimum algorithms that must succeed

logger = get_logger(__name__)


class Ensemble(BaseWorker):
    """Worker that detects anomalies using ensemble voting.
    
    Combines predictions from multiple anomaly detection algorithms:
    1. Local Outlier Factor (LOF) - Density-based
    2. One-Class SVM - Boundary-based
    3. Isolation Forest - Isolation-based
    
    An anomaly is flagged if it receives votes from a threshold fraction of successful algorithms.
    This ensemble approach increases robustness and reduces false positives.
    
    Advantages:
    - Combines different anomaly detection paradigms
    - More robust than single algorithms
    - Handles different types of anomalies better
    - Provides voting confidence scores
    
    Example:
        >>> worker = Ensemble()
        >>> df = pd.DataFrame({'value': [1, 2, 3, 100, 4, 5]})
        >>> result = worker.execute(df=df, threshold=0.5)
        >>> print(f"Anomalies: {result.data['anomalies_detected']}")
        Anomalies: 1
    """
    
    def __init__(self) -> None:
        """Initialize Ensemble with all sub-workers and error intelligence."""
        super().__init__("Ensemble")
        self.error_intelligence: ErrorIntelligence = ErrorIntelligence()
        self.logger = get_logger("Ensemble")
        
        # Initialize all workers
        self.lof: LOF = LOF()
        self.ocsvm: OneClassSVM = OneClassSVM()
        self.iso_forest: IFWorker = IFWorker()
    
    def execute(
        self,
        df: Optional[pd.DataFrame] = None,
        threshold: float = DEFAULT_THRESHOLD,
        **kwargs: Any
    ) -> WorkerResult:
        """Detect anomalies using ensemble voting.
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            threshold (float): Voting threshold (0-1). Default 0.5.
                - 0.5: Point is anomaly if >= 50% of algos agree
                - 0.33: Point is anomaly if >= 33% of algos agree (loose)
                - 1.0: Point is anomaly if 100% of algos agree (strict)
            **kwargs: Additional arguments
        
        Returns:
            WorkerResult: Ensemble detection results with:
                - anomalies_detected: Number of anomalies found
                - successful_algorithms: Number of algorithms that ran successfully
                - voting_breakdown: How many votes each anomaly received
        
        Example:
            >>> df = pd.DataFrame({'a': [1, 2, 3, 100], 'b': [10, 20, 30, 1000]})
            >>> result = worker.execute(df=df, threshold=0.33)
            >>> assert result.success
        """
        try:
            result: WorkerResult = self._run_ensemble(df, threshold, **kwargs)
            
            self.error_intelligence.track_success(
                agent_name="anomaly_detector",
                worker_name="Ensemble",
                operation="ensemble_detection",
                context={
                    "threshold": threshold,
                    "successful_algorithms": result.data.get('successful_algorithms', 0)
                }
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="anomaly_detector",
                worker_name="Ensemble",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"threshold": threshold}
            )
            raise
    
    def _run_ensemble(
        self,
        df: Optional[pd.DataFrame],
        threshold: float,
        **kwargs: Any
    ) -> WorkerResult:
        """Perform ensemble detection via voting.
        
        Args:
            df: Input DataFrame
            threshold: Voting threshold fraction
            **kwargs: Additional parameters
        
        Returns:
            WorkerResult with ensemble detection results
        """
        result: WorkerResult = self._create_result(
            task_type="ensemble_detection",
            quality_score=1.0
        )
        
        # ===== VALIDATE INPUTS =====
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
            result.success = False
            return result
        
        # Validate threshold parameter
        if not (0.0 < threshold <= 1.0):
            self._add_error(
                result,
                ErrorType.INVALID_PARAMETER,
                f"Threshold must be between 0 and 1, got {threshold}"
            )
            result.success = False
            return result
        
        try:
            # Extract numeric columns
            numeric_df: pd.DataFrame = df.select_dtypes(include=[np.number])
            if numeric_df.empty:
                self._add_error(result, ErrorType.LOAD_ERROR, "No numeric columns found")
                result.success = False
                return result
            
            # Initialize voting array
            votes: np.ndarray = np.zeros(len(numeric_df))
            successful_algos: int = 0
            algorithm_results: Dict[str, Any] = {}
            
            # ===== RUN LOF =====
            try:
                self.logger.info("Running LOF...")
                lof_result: WorkerResult = self.lof.safe_execute(
                    df=df,
                    n_neighbors=min(20, len(numeric_df) - 1),
                    contamination=0.1
                )
                if lof_result.success:
                    self.logger.info(f"LOF detected {lof_result.data.get('anomalies_detected', 0)} anomalies")
                    votes += 1
                    successful_algos += 1
                    algorithm_results['LOF'] = lof_result.data
                else:
                    self._add_warning(result, f"LOF failed: {lof_result.errors}")
            except Exception as e:
                self.logger.warning(f"LOF error in ensemble: {str(e)}")
                self._add_warning(result, f"LOF error: {str(e)}")
            
            # ===== RUN ONE-CLASS SVM =====
            try:
                self.logger.info("Running One-Class SVM...")
                ocsvm_result: WorkerResult = self.ocsvm.safe_execute(
                    df=df,
                    nu=0.05,
                    kernel='rbf'
                )
                if ocsvm_result.success:
                    self.logger.info(f"OCSVM detected {ocsvm_result.data.get('anomalies_detected', 0)} anomalies")
                    votes += 1
                    successful_algos += 1
                    algorithm_results['OneClassSVM'] = ocsvm_result.data
                else:
                    self._add_warning(result, f"OCSVM failed: {ocsvm_result.errors}")
            except Exception as e:
                self.logger.warning(f"One-Class SVM error in ensemble: {str(e)}")
                self._add_warning(result, f"One-Class SVM error: {str(e)}")
            
            # ===== RUN ISOLATION FOREST =====
            try:
                self.logger.info("Running Isolation Forest...")
                iso_result: WorkerResult = self.iso_forest.safe_execute(
                    df=df,
                    contamination=0.1,
                    n_estimators=100
                )
                if iso_result.success:
                    self.logger.info(f"Isolation Forest detected {iso_result.data.get('anomalies_detected', 0)} anomalies")
                    votes += 1
                    successful_algos += 1
                    algorithm_results['IsolationForest'] = iso_result.data
                else:
                    self._add_warning(result, f"Isolation Forest failed: {iso_result.errors}")
            except Exception as e:
                self.logger.warning(f"Isolation Forest error in ensemble: {str(e)}")
                self._add_warning(result, f"Isolation Forest error: {str(e)}")
            
            # ===== CHECK MINIMUM SUCCESSFUL ALGORITHMS =====
            if successful_algos < MIN_SUCCESSFUL_ALGOS:
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    f"All algorithms failed (need {MIN_SUCCESSFUL_ALGOS} to succeed)"
                )
                result.success = False
                return result
            
            # ===== CALCULATE VOTING THRESHOLD =====
            vote_threshold: float = max(1.0, threshold * successful_algos)
            ensemble_predictions: np.ndarray = votes >= vote_threshold
            
            # ===== CALCULATE STATISTICS =====
            anomaly_count: int = int(ensemble_predictions.sum())
            normal_count: int = len(ensemble_predictions) - anomaly_count
            anomaly_pct: float = (anomaly_count / len(ensemble_predictions) * 100) if len(ensemble_predictions) > 0 else 0
            
            # Calculate quality score
            quality_score: float = max(
                0.0,
                1.0 - (anomaly_count / len(ensemble_predictions)) if len(ensemble_predictions) > 0 else 0.0
            )
            result.quality_score = quality_score
            
            # ===== POPULATE RESULT DATA =====
            result.data = {
                "method": "Ensemble Voting",
                "threshold": threshold,
                "vote_threshold": vote_threshold,
                "successful_algorithms": successful_algos,
                "algorithms": ["LOF", "OneClassSVM", "IsolationForest"],
                "algorithm_results": algorithm_results,
                "sample_count": len(numeric_df),
                "anomalies_detected": anomaly_count,
                "anomalies_percentage": round(anomaly_pct, 2),
                "normal_count": normal_count,
                "vote_distribution": {
                    "0_votes": int((votes == 0).sum()),
                    "1_vote": int((votes == 1).sum()) if successful_algos >= 1 else 0,
                    "2_votes": int((votes == 2).sum()) if successful_algos >= 2 else 0,
                    "3_votes": int((votes == 3).sum()) if successful_algos >= 3 else 0,
                },
            }
            
            self.logger.info(
                f"Ensemble: {anomaly_count} anomalies ({anomaly_pct:.2f}%) detected "
                f"({successful_algos} successful algorithms)"
            )
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, f"Ensemble detection failed: {str(e)}")
            result.success = False
            self.logger.error(f"Error in ensemble detection: {str(e)}")
            return result
