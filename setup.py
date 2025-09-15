from setuptools import setup, find_packages

setup(
    name="forecast-generation-engine",
    version="1.0.0",
    author="Your Name",
    description="Microservice-based forecast generation engine",
    packages=find_packages(),
    install_requires=[
        "grpcio>=1.60.0",
        "grpcio-tools>=1.60.0",
        "protobuf>=4.25.1",
        "numpy>=1.24.3",
        "pandas>=2.0.3",
        "scipy>=1.11.1",
        "statsmodels>=0.14.0",
        "flask>=3.0.0",
        "scikit-learn>=1.3.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "forecast-preprocessing=services.data_preprocessing.server:serve",
            "forecast-segmentation=services.segmentation.server:serve",
            "forecast-outlier=services.outlier_cleansing.server:serve",
            "forecast-generation=services.forecast_generation.server:serve",
            "forecast-gateway=gateway.api_gateway:main",
        ],
    },
)