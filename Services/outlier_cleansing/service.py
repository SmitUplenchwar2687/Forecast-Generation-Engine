import numpy as np
import pandas as pd
from typing import Dict, Tuple, List
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OutlierCleanser:
    """Outlier detection and cleansing service."""
    
    def __init__(self):
        self.logger = logger
        
    def cleanse(self, data: np.ndarray, segmentation_result: Dict,
                parameters: Dict[str, float] = None) -> Tuple[np.ndarray, List[int], str, str]:
        """
        Cleanse outliers from time series data.
        
        Args:
            data: Time series values
            segmentation_result: Segmentation results
            parameters: Outlier detection parameters
            
        Returns:
            Tuple of (corrected_data, outlier_indices, method_used, correction_type)
        """
        default_params = {
            'sigma_multiplier': 3.0,
            'rolling_window': 6,
            'iqr_multiplier': 2.0,
            'correction_type': 'limit'  # 'limit' or 'interpolation'
        }
        
        if parameters:
            default_params.update(parameters)
        
        # Determine which method to use based on segmentation
        method = self._select_method(segmentation_result)
        
        # Detect outliers
        if method == 'Fixed Sigma':
            outlier_indices, bounds = self._fixed_sigma_detection(
                data, default_params['sigma_multiplier']
            )
        elif method == 'Rolling Sigma':
            outlier_indices, bounds = self._rolling_sigma_detection(
                data, default_params['rolling_window'], 
                default_params['sigma_multiplier']
            )
        else:  # Seasonal IQR
            outlier_indices, bounds = self._seasonal_iqr_detection(
                data, default_params['iqr_multiplier']
            )
        
        # Correct outliers
        corrected_data = self._correct_outliers(
            data.copy(), outlier_indices, bounds, 
            default_params['correction_type']
        )
        
        return corrected_data, outlier_indices, method, default_params['correction_type']
    
    def _select_method(self, segmentation_result: Dict) -> str:
        """Select outlier detection method based on segmentation."""
        trend = segmentation_result.get('trend', 'none')
        seasonal = segmentation_result.get('seasonal', False)
        
        if seasonal and trend != 'none':
            return 'Seasonal IQR'
        elif trend != 'none':
            return 'Rolling Sigma'
        else:
            return 'Fixed Sigma'
    
    def _fixed_sigma_detection(self, data: np.ndarray, 
                              sigma_multiplier: float) -> Tuple[List[int], Dict]:
        """Fixed sigma outlier detection."""
        mean = np.mean(data)
        std = np.std(data)
        
        upper_bound = mean + sigma_multiplier * std
        lower_bound = mean - sigma_multiplier * std
        
        outlier_indices = []
        for i, value in enumerate(data):
            if value > upper_bound or value < lower_bound:
                outlier_indices.append(i)
        
        bounds = {
            'upper': np.full(len(data), upper_bound),
            'lower': np.full(len(data), lower_bound)
        }
        
        return outlier_indices, bounds
    
    def _rolling_sigma_detection(self, data: np.ndarray, window: int,
                                sigma_multiplier: float) -> Tuple[List[int], Dict]:
        """Rolling sigma outlier detection."""
        df = pd.DataFrame({'value': data})
        
        # Calculate rolling statistics
        rolling_mean = df['value'].rolling(window=window, center=True).mean()
        rolling_std = df['value'].rolling(window=window, center=True).std()
        
        # Fill NaN values at edges
        rolling_mean = rolling_mean.fillna(method='bfill').fillna(method='ffill')
        rolling_std = rolling_std.fillna(method='bfill').fillna(method='ffill')
        
        upper_bound = rolling_mean + sigma_multiplier * rolling_std
        lower_bound = rolling_mean - sigma_multiplier * rolling_std
        
        outlier_indices = []
        for i, value in enumerate(data):
            if value > upper_bound.iloc[i] or value < lower_bound.iloc[i]:
                outlier_indices.append(i)
        
        bounds = {
            'upper': upper_bound.values,
            'lower': lower_bound.values
        }
        
        return outlier_indices, bounds
    
    def _seasonal_iqr_detection(self, data: np.ndarray,
                               iqr_multiplier: float) -> Tuple[List[int], Dict]:
        """Seasonal IQR outlier detection."""
        # Assume monthly data with yearly seasonality
        season_length = 12
        outlier_indices = []
        upper_bounds = np.zeros(len(data))
        lower_bounds = np.zeros(len(data))
        
        for month in range(season_length):
            # Get all values for this month across years
            month_indices = list(range(month, len(data), season_length))
            month_values = data[month_indices]
            
            if len(month_values) > 0:
                q1 = np.percentile(month_values, 25)
                q3 = np.percentile(month_values, 75)
                iqr = q3 - q1
                
                lower_bound = q1 - iqr_multiplier * iqr
                upper_bound = q3 + iqr_multiplier * iqr
                
                # Check for outliers in this month's values
                for idx in month_indices:
                    upper_bounds[idx] = upper_bound
                    lower_bounds[idx] = lower_bound
                    
                    if data[idx] > upper_bound or data[idx] < lower_bound:
                        outlier_indices.append(idx)
        
        bounds = {
            'upper': upper_bounds,
            'lower': lower_bounds
        }
        
        return outlier_indices, bounds
    
    def _correct_outliers(self, data: np.ndarray, outlier_indices: List[int],
                         bounds: Dict, correction_type: str) -> np.ndarray:
        """Correct identified outliers."""
        if correction_type == 'limit':
            # Replace outliers with threshold values
            for idx in outlier_indices:
                if data[idx] > bounds['upper'][idx]:
                    data[idx] = bounds['upper'][idx]
                elif data[idx] < bounds['lower'][idx]:
                    data[idx] = bounds['lower'][idx]
        
        elif correction_type == 'interpolation':
            # Interpolate outliers using neighboring values
            for idx in outlier_indices:
                prev_idx = idx - 1
                next_idx = idx + 1
                
                # Find valid neighboring values
                while prev_idx >= 0 and prev_idx in outlier_indices:
                    prev_idx -= 1
                while next_idx < len(data) and next_idx in outlier_indices:
                    next_idx += 1
                
                # Interpolate
                if prev_idx >= 0 and next_idx < len(data):
                    data[idx] = (data[prev_idx] + data[next_idx]) / 2
                elif prev_idx >= 0:
                    data[idx] = data[prev_idx]
                elif next_idx < len(data):
                    data[idx] = data[next_idx]
                # If no valid neighbors, use limit method
                else:
                    if data[idx] > bounds['upper'][idx]:
                        data[idx] = bounds['upper'][idx]
                    elif data[idx] < bounds['lower'][idx]:
                        data[idx] = bounds['lower'][idx]
        
        return data