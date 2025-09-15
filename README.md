# Forecast Generation Engine

A microservices-based forecasting system designed for scalable time series analysis and prediction. The engine provides modular components for data preprocessing, segmentation, outlier detection, and forecast generation through a unified API gateway.

## Architecture

The system follows a microservices architecture with the following components:

- **Data Preprocessing Service**: Handles data cleaning, transformation, and preparation
- **Segmentation Service**: Performs data segmentation and grouping operations
- **Outlier Cleansing Service**: Detects and handles anomalies in time series data
- **Forecast Generation Service**: Core forecasting engine using various prediction models
- **API Gateway**: Unified entry point for all services with request routing and orchestration

## Project Structure

```
forecast-generation-engine/
├── proto/                      # Protocol buffer definitions
│   └── forecast_service.proto
├── services/                   # Microservices
│   ├── data_preprocessing/     # Data cleaning and preparation
│   ├── segmentation/          # Data segmentation logic
│   ├── outlier_cleansing/     # Anomaly detection and cleaning
│   └── forecast_generation/   # Core forecasting algorithms
├── common/                    # Shared utilities and models
│   ├── models.py             # Data models and schemas
│   └── utils.py              # Common utilities
├── gateway/                   # API gateway
│   └── api_gateway.py
├── tests/                     # Unit and integration tests
├── docker-compose.yml         # Container orchestration
├── Dockerfile                 # Container definition
└── requirements.txt           # Python dependencies
```

## Features

- **Modular Design**: Each service handles a specific aspect of the forecasting pipeline
- **Scalable Architecture**: Microservices can be scaled independently based on demand
- **Protocol Buffer Communication**: Efficient inter-service communication
- **Containerized Deployment**: Docker support for easy deployment and scaling
- **Comprehensive Testing**: Full test coverage for all services
- **API Gateway**: Centralized request handling and service orchestration

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Protocol Buffers compiler (protoc)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd forecast-generation-engine
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate Protocol Buffer code:**
   ```bash
   protoc --python_out=. --grpc_python_out=. proto/forecast_service.proto
   ```

4. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

## Quick Start

### Using Docker Compose (Recommended)

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Verify services are running:**
   ```bash
   docker-compose ps
   ```

3. **Access the API gateway:**
   ```
   http://localhost:8000
   ```

### Manual Setup

1. **Start each service individually:**
   ```bash
   # Terminal 1 - Data Preprocessing
   cd services/data_preprocessing
   python server.py

   # Terminal 2 - Segmentation
   cd services/segmentation
   python server.py

   # Terminal 3 - Outlier Cleansing
   cd services/outlier_cleansing
   python server.py

   # Terminal 4 - Forecast Generation
   cd services/forecast_generation
   python server.py

   # Terminal 5 - API Gateway
   cd gateway
   python api_gateway.py
   ```

## API Usage

### Basic Forecast Request

```python
import requests

# Submit forecast request
response = requests.post('http://localhost:8000/forecast', json={
    'data': [...],  # Your time series data
    'config': {
        'horizon': 30,           # Forecast horizon
        'frequency': 'daily',    # Data frequency
        'model': 'auto'          # Model selection
    }
})

forecast_result = response.json()
```

### Pipeline Configuration

```python
# Custom pipeline configuration
config = {
    'preprocessing': {
        'remove_outliers': True,
        'fill_missing': 'interpolate',
        'normalize': True
    },
    'segmentation': {
        'method': 'seasonal',
        'segments': 4
    },
    'forecast': {
        'model': 'arima',
        'horizon': 60,
        'confidence_interval': 0.95
    }
}

response = requests.post('http://localhost:8000/forecast', json={
    'data': time_series_data,
    'config': config
})
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific service tests
python -m pytest tests/test_forecast_generation.py

# Run with coverage
python -m pytest tests/ --cov=services --cov-report=html
```

### Service Development

Each service follows a consistent structure:

- `server.py`: gRPC server implementation
- `service.py`: Business logic and core functionality
- `requirements.txt`: Service-specific dependencies

### Adding New Services

1. Create service directory under `services/`
2. Implement gRPC service interface
3. Add service configuration to `docker-compose.yml`
4. Update API gateway routing
5. Add corresponding tests

## Configuration

### Environment Variables

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARN, ERROR)
- `GRPC_PORT_*`: gRPC port for each service
- `GATEWAY_PORT`: API gateway port (default: 8000)
- `REDIS_URL`: Redis connection string for caching
- `DB_CONNECTION_STRING`: Database connection string

### Service Configuration

Each service can be configured through environment variables or config files placed in the service directory.

## Monitoring and Logging

- All services emit structured logs in JSON format
- Health check endpoints available at `/health` for each service
- Metrics collection compatible with Prometheus
- Distributed tracing support via OpenTelemetry

## Production Deployment

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -l app=forecast-engine
```

### Scaling Services

```bash
# Scale individual services
docker-compose up -d --scale forecast_generation=3
docker-compose up -d --scale data_preprocessing=2
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass before submitting PR

## Troubleshooting

### Common Issues

**Services not starting:**
- Check port conflicts
- Verify all dependencies are installed
- Check Docker daemon is running

**gRPC connection errors:**
- Verify service discovery configuration
- Check network connectivity between services
- Validate protocol buffer definitions

**Performance issues:**
- Monitor resource usage with `docker stats`
- Check service logs for bottlenecks
- Consider scaling problematic services

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Create an issue for bug reports or feature requests
- Check the [documentation](docs/) for detailed guides
- Join our [Slack channel](link-to-slack) for community support
