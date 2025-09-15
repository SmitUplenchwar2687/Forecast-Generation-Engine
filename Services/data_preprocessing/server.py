import grpc
from concurrent import futures
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import forecast_service_pb2
import forecast_service_pb2_grpc
from service import DataPreprocessor
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPreprocessingServicer(forecast_service_pb2_grpc.DataPreprocessingServiceServicer):
    """gRPC service implementation for data preprocessing."""
    
    def __init__(self):
        self.preprocessor = DataPreprocessor()
        
    def PreprocessData(self, request, context):
        """Process the preprocessing request."""
        try:
            # Extract data from request
            values = np.array(request.raw_data.values)
            timestamps = [ts.ToDatetime() for ts in request.raw_data.timestamps]
            config = dict(request.config)
            
            # Preprocess data
            processed_values, processed_timestamps = self.preprocessor.preprocess(
                values, timestamps, config
            )
            
            # Create response
            response = forecast_service_pb2.PreprocessResponse()
            response.processed_data.values.extend(processed_values.tolist())
            
            # Convert timestamps back to protobuf format
            for ts in processed_timestamps:
                timestamp = response.processed_data.timestamps.add()
                timestamp.FromDatetime(ts)
            
            response.success = True
            response.message = "Data preprocessing completed successfully"
            
            return response
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {str(e)}")
            response = forecast_service_pb2.PreprocessResponse()
            response.success = False
            response.message = f"Preprocessing failed: {str(e)}"
            return response

def serve():
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    forecast_service_pb2_grpc.add_DataPreprocessingServiceServicer_to_server(
        DataPreprocessingServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("Data Preprocessing Service started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()