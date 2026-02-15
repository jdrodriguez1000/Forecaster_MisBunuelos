
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
    parser.add_argument("--phase", type=str, help="Specify the phase to run (e.g., 'discovery', 'preprocessing', 'training')")
    args = parser.parse_args()
    
    print("Starting Forecaster Pipeline...")
    
    # 1. Discovery (Loader)
    if not args.phase or args.phase == "discovery":
        print("Running Phase 1: Data Discovery...")
        from src.loader import DataLoader
        loader = DataLoader(config)
        loader.run()

    # 2. Preprocessing
    if not args.phase or args.phase == "preprocessing":
        print("Running Phase 2: Preprocessing...")
        from src.preprocessor import Preprocessor
        preprocessor = Preprocessor(config)
        preprocessor.run()

if __name__ == "__main__":
    main()
