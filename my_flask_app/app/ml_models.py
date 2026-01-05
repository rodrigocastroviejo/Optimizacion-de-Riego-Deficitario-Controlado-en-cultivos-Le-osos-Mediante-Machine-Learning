import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.vector_ar.var_model import VAR
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

class SarimaModel(BaseEstimator, TransformerMixin):
    """Wrapper de SARIMA para scikit-learn"""
    
    def __init__(self, column: str = None, order: tuple = (1,1,1), 
                 seasonal_order: tuple = (1,1,1,30), trend: str = 'c'):
        self.column = column
        self.order = order
        self.seasonal_order = seasonal_order
        self.trend = trend
        self.model = None
        self.fitted_model = None
        
    def fit(self, X, y=None):
        if self.column is None and isinstance(X, pd.DataFrame):
            self.column = X.columns[0]
            
        if isinstance(X, pd.DataFrame):
            series = X[self.column]
        else:
            series = X
            
        self.model = SARIMAX(series, 
                           order=self.order,
                           seasonal_order=self.seasonal_order,
                           trend=self.trend,
                           enforce_stationarity=False,
                           enforce_invertibility=False)
        
        self.fitted_model = self.model.fit(disp=False)
        return self
    
    def predict(self, X, n_periods: int = 30):
        if isinstance(X, pd.DataFrame) and self.column:
            # Usar el último valor de la columna
            last_value = X[self.column].iloc[-1]
        else:
            last_value = X.iloc[-1] if isinstance(X, pd.Series) else X[-1]
        
        # Para predicción simple, no necesitamos X completa
        forecast = self.fitted_model.get_forecast(steps=n_periods)
        return forecast.predicted_mean
    
    def get_params(self, deep=True):
        return {'column': self.column, 
                'order': self.order, 
                'seasonal_order': self.seasonal_order,
                'trend': self.trend}
    
    def set_params(self, **parameters):
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self

class SarimaxModel(BaseEstimator, TransformerMixin):
    """Wrapper de SARIMAX para scikit-learn"""
    
    def __init__(self, target_col: str = None, exog_cols: list = None, 
                 order: tuple = (1,1,1), seasonal_order: tuple = (1,1,1,30)):
        self.target_col = target_col
        self.exog_cols = exog_cols if exog_cols else []
        self.order = order
        self.seasonal_order = seasonal_order
        self.model = None
        self.fitted_model = None
        
    def fit(self, X, y=None):
        if self.target_col is None and isinstance(X, pd.DataFrame):
            self.target_col = X.columns[0]
        
        if not self.exog_cols and isinstance(X, pd.DataFrame):
            self.exog_cols = [col for col in X.columns if col != self.target_col][:3]
        
        endog = X[self.target_col]
        exog = X[self.exog_cols]
        
        self.model = SARIMAX(endog, exog=exog,
                           order=self.order,
                           seasonal_order=self.seasonal_order,
                           enforce_stationarity=False,
                           enforce_invertibility=False)
        
        self.fitted_model = self.model.fit(disp=False)
        return self
    
    def predict(self, X, n_periods: int = 30):
        if len(X) < n_periods:
            # Extender las variables exógenas usando el último valor
            exog_future = pd.DataFrame(np.tile(X[self.exog_cols].iloc[-1:].values, 
                                              (n_periods, 1)),
                                      columns=self.exog_cols)
        else:
            exog_future = X[self.exog_cols].iloc[:n_periods]
        
        forecast = self.fitted_model.get_forecast(steps=n_periods, exog=exog_future)
        return forecast.predicted_mean

class VarModel(BaseEstimator, TransformerMixin):
    """Wrapper de VAR para scikit-learn"""
    
    def __init__(self, maxlags: int = 15, ic: str = 'aic'):
        self.maxlags = maxlags
        self.ic = ic
        self.model = None
        self.fitted_model = None
        
    def fit(self, X, y=None):
        self.model = VAR(X)
        self.fitted_model = self.model.fit(maxlags=self.maxlags, ic=self.ic)
        return self
    
    def predict(self, X, n_periods: int = 30):
        lag_order = self.fitted_model.k_ar
        last_observations = X.values[-lag_order:]
        
        forecast = self.fitted_model.forecast(y=last_observations, steps=n_periods)
        return pd.DataFrame(forecast, columns=X.columns)
    
    def get_params(self, deep=True):
        return {'maxlags': self.maxlags, 'ic': self.ic}
    
    def set_params(self, **parameters):
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self

class LSTMModel(BaseEstimator, TransformerMixin):
    """Wrapper de LSTM multivariante para scikit-learn"""
    
    def __init__(self, sequence_length: int = 30, lstm_units: list = [50, 25],
                 dropout_rate: float = 0.2, learning_rate: float = 0.001,
                 epochs: int = 50, batch_size: int = 16):
        
        self.sequence_length = sequence_length
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.model = None
        self.scaler = None
        self.last_sequence = None
        self.feature_names = None
        
    def fit(self, X, y=None):
        self.feature_names = X.columns.tolist()
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = self.scaler.fit_transform(X)
        
        X_seq, y_seq = self._create_sequences(scaled_data)
        self.last_sequence = X_seq[-1:].copy()
        
        self.model = self._build_model(X_seq.shape[1:], y_seq.shape[1])
        
        self.model.fit(
            X_seq, y_seq,
            epochs=self.epochs,
            batch_size=self.batch_size,
            verbose=0,
            shuffle=False
        )
        
        return self
    
    def _create_sequences(self, data):
        X, y = [], []
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i])
        return np.array(X), np.array(y)
    
    def _build_model(self, input_shape, output_dim):
        model = Sequential()
        
        # Capa LSTM
        model.add(LSTM(
            units=self.lstm_units[0],
            return_sequences=len(self.lstm_units) > 1,
            input_shape=input_shape
        ))
        model.add(Dropout(self.dropout_rate))
        
        # Capas LSTM adicionales
        for units in self.lstm_units[1:]:
            model.add(LSTM(units=units, return_sequences=False))
            model.add(Dropout(self.dropout_rate))
        
        # Capa de salida
        model.add(Dense(output_dim))
        
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='mse'
        )
        
        return model
    
    def predict(self, X, n_periods: int = 30):
        scaled_data = self.scaler.transform(X)
        
        if self.last_sequence is None:
            last_sequence = scaled_data[-self.sequence_length:]
            last_sequence = last_sequence.reshape(1, self.sequence_length, -1)
        else:
            last_sequence = self.last_sequence
        
        predictions_scaled = []
        current_sequence = last_sequence.copy()
        
        for _ in range(n_periods):
            next_step = self.model.predict(current_sequence, verbose=0)
            predictions_scaled.append(next_step[0])
            current_sequence = np.roll(current_sequence, -1, axis=1)
            current_sequence[0, -1, :] = next_step[0]
        
        predictions = self.scaler.inverse_transform(np.array(predictions_scaled))
        return pd.DataFrame(predictions, columns=self.feature_names)
    
    def get_params(self, deep=True):
        return {
            'sequence_length': self.sequence_length,
            'lstm_units': self.lstm_units,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate,
            'epochs': self.epochs,
            'batch_size': self.batch_size
        }
    
    def set_params(self, **parameters):
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self