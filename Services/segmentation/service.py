import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SegmentationResult:
    volume_class: str
    cov_class: str
    intermittent: bool
    density: float
    series_length: int
    plc_status: str
    trend: str
    seasonal: bool
    rule_number: int
    volume_percentage: float
    coefficient_variation: float

class SegmentationEngine:
    """Segmentation engine for time series classification."""
    
    def __init__(self):
        self.logger = logger
        self.default_thresholds = {
            'volume_a_threshold': 85.0,
            'volume_b_threshold': 95.0,
            'cov_threshold': 0.5,
            'intermittent_threshold': 0.5,
            'trend_threshold': 0.05,
            'seasonality_threshold': 0.1
        }
    
    def segment(self, data: np.ndarray, history_months: int = 12,
                thresholds: Dict[str, float] = None) -> SegmentationResult:
        """
        Perform segmentation on time series data.
        
        Args:
            data: Time series values
            history_months: Number of months to use for segmentation
            thresholds: Custom threshold values
            
        Returns:
            SegmentationResult object
        """
        if thresholds:
            self.default_thresholds.update(thresholds)
        
        # Use last n months for segmentation
        segmentation_data = data[-history_months:] if len(data) > history_months else data
        
        # Step 1: Volume Arrangement
        volume_class, volume_pct = self._calculate_volume_class(segmentation_data)
        
        # Step 2: Coefficient of Variability
        cov_class, cov_value = self._calculate_cov_class(segmentation_data)
        
        # Step 3: Intermittency and Density
        intermittent, density = self._check_intermittency(segmentation_data)
        
        # Step 4: Additional Outputs
        series_length = len(data)
        plc_status = self._determine_plc_status(data)
        trend = self._detect_trend(segmentation_data)
        seasonal = self._detect_seasonality(data)
        
        # Step 5: Assignment of Rules
        rule_number = self._assign_rule(
            intermittent, plc_status, cov_class, volume_class, 
            trend, seasonal
        )
        
        return SegmentationResult(
            volume_class=volume_class,
            cov_class=cov_class,
            intermittent=intermittent,
            density=density,
            series_length=series_length,
            plc_status=plc_status,
            trend=trend,
            seasonal=seasonal,
            rule_number=rule_number,
            volume_percentage=volume_pct,
            coefficient_variation=cov_value
        )
    
    def _calculate_volume_class(self, data: np.ndarray) -> Tuple[str, float]:
        """Calculate volume class based on cumulative percentage."""
        total_volume = np.sum(np.abs(data))
        
        if total_volume == 0:
            return 'C', 0.0
        
        # Sort in descending order
        sorted_data = np.sort(np.abs(data))[::-1]
        cumulative_sum = np.cumsum(sorted_data)
        cumulative_pct = (cumulative_sum / total_volume) * 100
        
        # Find the percentage for this item
        item_pct = cumulative_pct[-1] if len(cumulative_pct) > 0 else 0
        
        # Classify based on thresholds
        if item_pct <= self.default_thresholds['volume_a_threshold']:
            return 'A', item_pct
        elif item_pct <= self.default_thresholds['volume_b_threshold']:
            return 'B', item_pct
        else:
            return 'C', item_pct
    
    def _calculate_cov_class(self, data: np.ndarray) -> Tuple[str, float]:
        """Calculate coefficient of variation class."""
        mean_val = np.mean(data)
        std_val = np.std(data)
        
        if mean_val == 0:
            cov = float('inf')
        else:
            cov = std_val / abs(mean_val)
        
        if cov < self.default_thresholds['cov_threshold']:
            return 'X', cov
        else:
            return 'Y', cov
    
    def _check_intermittency(self, data: np.ndarray) -> Tuple[bool, float]:
        """Check if data is intermittent and calculate density."""
        zero_count = np.sum(data == 0)
        total_count = len(data)
        
        zero_percentage = zero_count / total_count if total_count > 0 else 0
        density = 1 - zero_percentage
        
        intermittent = zero_percentage > self.default_thresholds['intermittent_threshold']
        
        return intermittent, density
    
    def _determine_plc_status(self, data: np.ndarray) -> str:
        """Determine Product Life Cycle status."""
        if len(data) < 6:
            return 'New Launch'
        
        # Check for discontinuous pattern
        recent_data = data[-6:]
        if np.sum(recent_data == 0) >= 4:
            return 'Discontinuous'
        
        # Check for new launch pattern (increasing trend in recent data)
        if len(data) < 12:
            return 'New Launch'
        
        return 'Mature'
    
    def _detect_trend(self, data: np.ndarray) -> str:
        """Detect trend in the data."""
        if len(data) < 2:
            return 'none'
        
        # Calculate linear regression slope
        x = np.arange(len(data))
        coefficients = np.polyfit(x, data, 1)
        slope = coefficients[0]
        
        # Normalize slope by mean
        mean_val = np.mean(np.abs(data))
        if mean_val > 0:
            normalized_slope = slope / mean_val
        else:
            normalized_slope = 0
        
        if abs(normalized_slope) < self.default_thresholds['trend_threshold']:
            return 'none'
        elif normalized_slope > 0:
            return 'upward'
        else:
            return 'downward'
    
    def _detect_seasonality(self, data: np.ndarray) -> bool:
        """Detect seasonality in the data."""
        if len(data) < 24:  # Need at least 2 years of data
            return False
        
        # Simple seasonality detection using autocorrelation
        # Check for 12-month seasonality
        if len(data) >= 24:
            season_length = 12
            autocorr = np.corrcoef(data[:-season_length], data[season_length:])[0, 1]
            return autocorr > self.default_thresholds['seasonality_threshold']
        
        return False
    
    def _assign_rule(self, intermittent: bool, plc_status: str, 
                    cov_class: str, volume_class: str,
                    trend: str, seasonal: bool) -> int:
        """Assign rule number based on segmentation results."""
        if intermittent:
            return 1
        
        if plc_status == 'Discontinuous':
            return 2
        
        if plc_status == 'New Launch':
            return 3
        
        if cov_class == 'X':
            return 4
        
        if volume_class == 'C':
            return 5
        
        if trend != 'none':
            return 6
        
        if seasonal:
            return 7
        
        return 8  # No match