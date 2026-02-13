import argparse
from src.utils import load_config, setup_logging

def main():
    """
    Main orchestrator for the forecasting pipeline.
    """
    # Load configuration
    config = load_config()
    setup_logging()
    
    # Parse arguments provided by the user (if any)
    parser = argparse.ArgumentParser(description="Forecaster Mis Bunuelos Orchestrator")
    parser.add_argument("--phase", type=str, help="Specify the phase to run (e.g., 'preprocessing', 'training')")
    args = parser.parse_args()
    
    print("Starting Forecaster Pipeline...")
    
    # TODO: Orchestrate the pipeline execution based on arguments or config
    # 1. Discovery (Loader)
    # 2. Preprocessing
    # 3. Features
    # 4. Modeling

if __name__ == "__main__":
    main()
