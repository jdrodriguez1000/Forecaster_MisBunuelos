import pandas as pd
from skforecast.ForecasterDirect import ForecasterDirect

def train_model(train_data: pd.DataFrame, config: dict):
    """
    Trains the forecasting model using skforecast.
    
    Args:
        train_data (pd.DataFrame): The training dataset.
        config (dict): Configuration parameters for the model.
        
    Returns:
        The trained forecaster object.
    """
    # TODO: Implement model training with ForecasterDirect
    pass

def backtest_model(forecaster, y: pd.Series, initial_train_size: int, steps: int):
    """
    Performs rolling backtesting on the model.
    
    Args:
        forecaster: The trained forecaster object.
        y (pd.Series): The target time series.
        initial_train_size (int): Size of the initial training set.
        steps (int): Forecast horizon.

    Returns:
        metric, predictions
    """
    # TODO: Implement backtesting
    pass
