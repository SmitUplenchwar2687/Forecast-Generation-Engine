import grpc
from flask import Flask, request, jsonify
import numpy as np
from datetime import datetime
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import forecast_service_pb2
import forecast_service_pb2_grpc

app = Flask(__name__)

# gRPC channel configuration
PREPROCESSING_SERVICE = 'localhost:50051'
SEGMENTATION_SERVICE = 'localhost:50052'
OUTLIER_SERVICE = 'localhost:50053'
FORECAST_SERVICE = 'localhost:50054'

class ForecastPipeline:
    """Orchestrate the forecast generation pipeline."""
    
    def __init__(self):
        # Create gRPC channels
        self.preprocessing_channel = grpc.insecure_channel(PREPROCESSING_SERVICE)
        self.segmentation_channel = grpc.insecure_channel(SEGMENTATION_SERVICE)
        self.outlier_channel = grpc.insecure_channel(OUTLIER_SERVICE)
        self.forecast_channel = grpc.insecure_channel(FORECAST_SERVICE)
        
        # Create stubs
        self.preprocessing_stub = forecast_service_pb2_grpc.DataPreprocessingServiceStub(
            self.preprocessing_channel
        )
        self.segmentation_stub = forecast_service_pb2_grpc.SegmentationServiceStub(
            self.segmentation_channel
        )
        self.outlier_stub = forecast_service_pb2_grpc.OutlierCleansingServiceStub(
            self.outlier_channel
        )
        self.forecast_stub = forecast_service_pb2_grpc.ForecastGenerationServiceStub(
            self.forecast_channel
        )
    
    def generate_forecast(self, data, timestamps, config):
        """Execute the full forecast pipeline."""
        results = {}
        
        # Step 1: Data Preprocessing
        preprocess_request = forecast_service_pb2.PreprocessRequest()
        preprocess_request.raw_data.values.extend(data)
        for ts in timestamps:
            timestamp = preprocess_request.raw_data.timestamps.add()
            timestamp.FromDatetime(ts)
        preprocess_request.config.update(config.get('preprocessing', {}))
        
        preprocess_response = self.preprocessing_stub.PreprocessData(preprocess_request)
        if not preprocess_response.success:
            return {'error': preprocess_response.message}
        
        results['preprocessing'] = {
            'success': preprocess_response.success,
            'message': preprocess_response.message
        }
        
        # Step 2: Segmentation
        segment_request = forecast_service_pb2.SegmentRequest()
        segment_request.data.CopyFrom(preprocess_response.processed_data)
        segment_request.history_months = config.get('history_months', 12)
        segment_request.thresholds.update(config.get('thresholds', {}))
        
        segment_response = self.segmentation_stub.SegmentData(segment_request)
        if not segment_response.success:
            return {'error': segment_response.message}
        
        results['segmentation'] = {
            'volume_class': segment_response.result.volume_class,
            'cov_class': segment_response.result.cov_class,
            'rule_number': segment_response.result.rule_number,
            'intermittent': segment_response.result.intermittent,
            'plc_status': segment_response.result.plc_status,
            'trend': segment_response.result.trend,
            'seasonal': segment_response.result.seasonal
        }
        
        # Step 3: Outlier Cleansing
        outlier_request = forecast_service_pb2.OutlierRequest()
        outlier_request.data.CopyFrom(preprocess_response.processed_data)
        outlier_request.segmentation.CopyFrom(segment_response.result)
        outlier_request.parameters.update(config.get('outlier_params', {}))
        
        outlier_response = self.outlier_stub.CleanseOutliers(outlier_request)
        if not outlier_response.success:
            return {'error': outlier_response.message}
        
        results['outlier_cleansing'] = {
            'method_used': outlier_response.result.method_used,
            'correction_type': outlier_response.result.correction_type,
            'outliers_found': len(outlier_response.result.outlier_indices)
        }
        
        # Step 4: Forecast Generation
        forecast_request = forecast_service_pb2.ForecastRequest()
        forecast_request.historical_data.CopyFrom(
            outlier_response.result.corrected_series
        )
        forecast_request.cleansed_data.CopyFrom(outlier_response.result)
        forecast_request.segmentation.CopyFrom(segment_response.result)
        forecast_request.forecast_horizon = config.get('forecast_horizon', 12)
        forecast_request.config.update(config.get('forecast_config', {}))
        
        forecast_response = self.forecast_stub.GenerateForecast(forecast_request)
        if not forecast_response.success:
            return {'error': forecast_response.message}
        
        results['forecast'] = {
            'algorithm_used': forecast_response.result.algorithm_used,
            'forecast_values': list(forecast_response.result.forecast_values),
            'mape': forecast_response.result.mape,
            'rmse': forecast_response.result.rmse
        }
        
        return results

pipeline = ForecastPipeline()

@app.route('/forecast', methods=['POST'])
def forecast():
    """API endpoint for forecast generation."""
    try:
        request_data = request.json
        
        # Extract data
        values = request_data.get('values', [])
        timestamps = [datetime.fromisoformat(ts) for ts in request_data.get('timestamps', [])]
        config = request_data.get('config', {})
        
        # Generate forecast
        result = pipeline.generate_forecast(values, timestamps, config)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)