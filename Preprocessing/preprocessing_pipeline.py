"""
Comprehensive Preprocessing Pipeline for ESG-Financial Clustering Analysis

This module implements a reproducible, modular preprocessing pipeline designed for
sustainability clustering applications. The pipeline handles mixed data types,
applies appropriate transformations, and ensures consistent results across
different datasets and computing environments.

Author: ESG Clustering Analysis Project
Date: October 2025
Version: 1.0.0
"""

import pandas as pd
import numpy as np
import joblib
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union, Optional
from datetime import datetime

# Core preprocessing
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler,
    OneHotEncoder, LabelEncoder, PowerTransformer
)
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.model_selection import train_test_split

# Statistical analysis
from scipy import stats
from scipy.stats import skew

# Data validation
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ESGPreprocessingPipeline:
    """
    Comprehensive preprocessing pipeline for ESG-Financial clustering data.
    
    This class implements a modular, reproducible preprocessing pipeline that:
    - Handles missing values with configurable strategies
    - Applies power transformations to reduce skewness
    - Scales features using multiple scaling methods
    - Encodes categorical variables with one-hot encoding
    - Performs dimensionality reduction (PCA, t-SNE)
    - Saves and loads fitted transformers for consistency
    - Validates pipeline outputs with automated tests
    
    Features:
    - Reproducible: Same results across runs and environments
    - Configurable: Parameters stored in external config files
    - Modular: Separate components for different preprocessing tasks
    - Validated: Automated tests ensure data quality
    - Documented: Transparent preprocessing decisions
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the preprocessing pipeline.
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
        """
        self.config = self._load_config(config_path)
        self.pipeline_components = {}
        self.feature_names_ = {}
        self.preprocessing_log = []
        self.fitted = False
        
        # Initialize component storage
        self.power_transformer = None
        self.scaler = None
        self.categorical_encoder = None
        self.pca = None
        self.tsne = None
        
        logger.info("ESG Preprocessing Pipeline initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults."""
        default_config = {
            'preprocessing': {
                'missing_strategy_numerical': 'median',
                'missing_strategy_categorical': 'most_frequent',
                'scaling_method': 'standard',
                'apply_power_transform': True,
                'power_transform_method': 'yeo-johnson',
                'skewness_threshold': 1.0,
                'categorical_encoding': 'onehot',
                'drop_first_category': True
            },
            'dimensionality_reduction': {
                'apply_pca': True,
                'pca_n_components': 0.95,  # Explained variance threshold
                'pca_min_components': 5,
                'apply_tsne': True,
                'tsne_n_components': 2,
                'tsne_perplexity': 30,
                'tsne_random_state': 42
            },
            'feature_categories': {
                'financial_features': ['Revenue', 'ProfitMargin', 'MarketCap', 'GrowthRate'],
                'esg_features': ['ESG_Overall', 'ESG_Environmental', 'ESG_Social', 'ESG_Governance'],
                'environmental_features': ['CarbonEmissions', 'WaterUsage', 'EnergyConsumption'],
                'categorical_features': ['Industry', 'Region'],
                'identifier_features': ['CompanyID', 'CompanyName', 'Year']
            },
            'validation': {
                'check_missing_values': True,
                'check_feature_ranges': True,
                'check_shape_consistency': True,
                'log_transformations': True
            },
            'output': {
                'save_intermediate_steps': True,
                'save_path': '../Data/',
                'save_fitted_pipeline': True,
                'pipeline_save_path': '../Models/'
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                        user_config = yaml.safe_load(f)
                    else:
                        user_config = json.load(f)
                
                # Merge with defaults
                self._deep_update(default_config, user_config)
                logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
                logger.info("Using default configuration")
        else:
            logger.info("Using default configuration")
        
        return default_config
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """Recursively update nested dictionaries."""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict:
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _log_step(self, step: str, details: str) -> None:
        """Log preprocessing step with timestamp."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'details': details
        }
        self.preprocessing_log.append(log_entry)
        logger.info(f"{step}: {details}")
    
    def _identify_feature_types(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Automatically identify feature types from dataframe."""
        feature_categories = self.config['feature_categories']
        
        # Get available columns
        available_cols = df.columns.tolist()
        
        # Filter feature categories to only include available columns
        identified_features = {}
        for category, features in feature_categories.items():
            identified_features[category] = [f for f in features if f in available_cols]
        
        # Identify numerical and categorical features automatically
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Remove identifier columns from numerical features
        numerical_cols = [col for col in numerical_cols 
                         if col not in identified_features['identifier_features']]
        
        identified_features['numerical_features'] = numerical_cols
        identified_features['categorical_features_available'] = categorical_cols
        
        self._log_step("Feature Identification", 
                      f"Numerical: {len(numerical_cols)}, Categorical: {len(categorical_cols)}")
        
        return identified_features
    
    def _handle_missing_values(self, df: pd.DataFrame, 
                              feature_types: Dict[str, List[str]]) -> pd.DataFrame:
        """Handle missing values according to configuration."""
        df_clean = df.copy()
        missing_info = {}
        
        # Check for missing values
        missing_counts = df_clean.isnull().sum()
        missing_features = missing_counts[missing_counts > 0]
        
        if len(missing_features) > 0:
            self._log_step("Missing Values Detection", 
                          f"Found missing values in {len(missing_features)} features")
            
            # Handle numerical missing values
            numerical_missing = [col for col in missing_features.index 
                               if col in feature_types['numerical_features']]
            
            if numerical_missing:
                strategy = self.config['preprocessing']['missing_strategy_numerical']
                for col in numerical_missing:
                    if strategy == 'median':
                        fill_value = df_clean[col].median()
                    elif strategy == 'mean':
                        fill_value = df_clean[col].mean()
                    else:  # mode
                        fill_value = df_clean[col].mode().iloc[0] if not df_clean[col].mode().empty else 0
                    
                    df_clean[col].fillna(fill_value, inplace=True)
                    missing_info[col] = {'strategy': strategy, 'fill_value': fill_value}
            
            # Handle categorical missing values
            categorical_missing = [col for col in missing_features.index 
                                 if col in feature_types['categorical_features_available']]
            
            if categorical_missing:
                strategy = self.config['preprocessing']['missing_strategy_categorical']
                for col in categorical_missing:
                    if strategy == 'most_frequent':
                        fill_value = df_clean[col].mode().iloc[0] if not df_clean[col].mode().empty else 'Unknown'
                    else:
                        fill_value = 'Unknown'
                    
                    df_clean[col].fillna(fill_value, inplace=True)
                    missing_info[col] = {'strategy': strategy, 'fill_value': fill_value}
            
            self._log_step("Missing Values Handling", 
                          f"Imputed {len(missing_info)} features: {list(missing_info.keys())}")
        else:
            self._log_step("Missing Values Check", "No missing values found")
        
        return df_clean
    
    def _apply_power_transformation(self, X: np.ndarray, 
                                   feature_names: List[str]) -> Tuple[np.ndarray, PowerTransformer]:
        """Apply power transformation to reduce skewness."""
        if not self.config['preprocessing']['apply_power_transform']:
            return X, None
        
        # Check skewness
        skewness_threshold = self.config['preprocessing']['skewness_threshold']
        original_skew = {}
        high_skew_features = []
        
        for i, feature in enumerate(feature_names):
            skew_value = skew(X[:, i])
            original_skew[feature] = skew_value
            if abs(skew_value) >= skewness_threshold:
                high_skew_features.append(feature)
        
        if not high_skew_features:
            self._log_step("Skewness Analysis", "No highly skewed features found")
            return X, None
        
        # Apply power transformation
        method = self.config['preprocessing']['power_transform_method']
        power_transformer = PowerTransformer(method=method, standardize=False)
        X_transformed = power_transformer.fit_transform(X)
        
        # Log improvements
        improvements = {}
        for i, feature in enumerate(feature_names):
            if feature in high_skew_features:
                new_skew = skew(X_transformed[:, i])
                improvement = abs(original_skew[feature]) - abs(new_skew)
                improvements[feature] = {
                    'original_skew': original_skew[feature],
                    'new_skew': new_skew,
                    'improvement': improvement
                }
        
        self._log_step("Power Transformation", 
                      f"Applied {method} to {len(high_skew_features)} features")
        
        return X_transformed, power_transformer
    
    def _apply_scaling(self, X: np.ndarray) -> Tuple[np.ndarray, object]:
        """Apply scaling to numerical features."""
        scaling_method = self.config['preprocessing']['scaling_method']
        
        if scaling_method == 'standard':
            scaler = StandardScaler()
        elif scaling_method == 'robust':
            scaler = RobustScaler()
        elif scaling_method == 'minmax':
            scaler = MinMaxScaler()
        else:
            logger.warning(f"Unknown scaling method: {scaling_method}. Using StandardScaler.")
            scaler = StandardScaler()
        
        X_scaled = scaler.fit_transform(X)
        
        self._log_step("Feature Scaling", f"Applied {scaler.__class__.__name__}")
        
        return X_scaled, scaler
    
    def _encode_categorical_features(self, df: pd.DataFrame, 
                                   categorical_features: List[str]) -> Tuple[np.ndarray, List[str], OneHotEncoder]:
        """Encode categorical features."""
        if not categorical_features:
            return np.array([]).reshape(len(df), 0), [], None
        
        encoding_method = self.config['preprocessing']['categorical_encoding']
        
        if encoding_method == 'onehot':
            encoder = OneHotEncoder(
                drop='first' if self.config['preprocessing']['drop_first_category'] else None,
                sparse_output=False,
                handle_unknown='ignore'
            )
            
            X_categorical = encoder.fit_transform(df[categorical_features])
            
            # Get feature names
            feature_names = encoder.get_feature_names_out(categorical_features)
            
            self._log_step("Categorical Encoding", 
                          f"One-hot encoded {len(categorical_features)} features into {len(feature_names)} features")
            
            return X_categorical, list(feature_names), encoder
        
        else:
            logger.warning(f"Encoding method {encoding_method} not implemented. Skipping categorical encoding.")
            return np.array([]).reshape(len(df), 0), [], None
    
    def _apply_dimensionality_reduction(self, X: np.ndarray, 
                                      feature_names: List[str]) -> Dict[str, Tuple[np.ndarray, object]]:
        """Apply dimensionality reduction techniques."""
        reduction_results = {}
        
        # PCA
        if self.config['dimensionality_reduction']['apply_pca']:
            n_components = self.config['dimensionality_reduction']['pca_n_components']
            min_components = self.config['dimensionality_reduction']['pca_min_components']
            
            # Handle different n_components specifications
            if isinstance(n_components, float) and n_components <= 1.0:
                # Use explained variance ratio
                pca = PCA(n_components=None)
                pca.fit(X)
                
                # Find number of components for desired explained variance
                cumsum_var = np.cumsum(pca.explained_variance_ratio_)
                n_comp = np.argmax(cumsum_var >= n_components) + 1
                n_comp = max(n_comp, min_components)  # Ensure minimum components
                
                # Refit with determined number of components
                pca = PCA(n_components=n_comp)
                X_pca = pca.fit_transform(X)
                
                explained_var = np.sum(pca.explained_variance_ratio_)
                
            else:
                # Use explicit number of components
                n_comp = int(n_components) if isinstance(n_components, float) else n_components
                pca = PCA(n_components=n_comp)
                X_pca = pca.fit_transform(X)
                explained_var = np.sum(pca.explained_variance_ratio_)
            
            pca_feature_names = [f'PCA_{i+1}' for i in range(X_pca.shape[1])]
            reduction_results['pca'] = (X_pca, pca)
            
            self._log_step("PCA Application", 
                          f"Reduced to {X_pca.shape[1]} components, explained variance: {explained_var:.3f}")
        
        # t-SNE
        if self.config['dimensionality_reduction']['apply_tsne']:
            n_components = self.config['dimensionality_reduction']['tsne_n_components']
            perplexity = self.config['dimensionality_reduction']['tsne_perplexity']
            random_state = self.config['dimensionality_reduction']['tsne_random_state']
            
            # Use PCA results if available, otherwise use original data
            X_for_tsne = reduction_results['pca'][0] if 'pca' in reduction_results else X
            
            tsne = TSNE(
                n_components=n_components,
                perplexity=min(perplexity, (len(X) - 1) // 3),  # Adjust perplexity if needed
                random_state=random_state
            )
            X_tsne = tsne.fit_transform(X_for_tsne)
            
            tsne_feature_names = [f't-SNE_{i+1}' for i in range(X_tsne.shape[1])]
            reduction_results['tsne'] = (X_tsne, tsne)
            
            self._log_step("t-SNE Application", 
                          f"Reduced to {X_tsne.shape[1]} components for visualization")
        
        return reduction_results
    
    def fit_transform(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Fit the preprocessing pipeline and transform the data.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dictionary containing transformed datasets
        """
        logger.info("Starting preprocessing pipeline fitting and transformation")
        
        # Step 1: Identify feature types
        feature_types = self._identify_feature_types(df)
        
        # Step 2: Handle missing values
        df_clean = self._handle_missing_values(df, feature_types)
        
        # Step 3: Separate numerical and categorical features
        numerical_features = feature_types['numerical_features']
        categorical_features = feature_types['categorical_features_available']
        
        # Extract numerical data
        X_numerical = df_clean[numerical_features].values
        
        # Step 4: Apply power transformation
        X_power_transformed, self.power_transformer = self._apply_power_transformation(
            X_numerical, numerical_features
        )
        
        # Use power transformed data if available
        X_to_scale = X_power_transformed if X_power_transformed is not None else X_numerical
        
        # Step 5: Apply scaling
        X_scaled, self.scaler = self._apply_scaling(X_to_scale)
        
        # Step 6: Encode categorical features
        X_categorical, categorical_feature_names, self.categorical_encoder = self._encode_categorical_features(
            df_clean, categorical_features
        )
        
        # Step 7: Combine numerical and categorical features
        if X_categorical.shape[1] > 0:
            X_combined = np.hstack([X_scaled, X_categorical])
            combined_feature_names = numerical_features + categorical_feature_names
        else:
            X_combined = X_scaled
            combined_feature_names = numerical_features
        
        # Step 8: Apply dimensionality reduction
        reduction_results = self._apply_dimensionality_reduction(X_combined, combined_feature_names)
        
        # Store results
        results = {}
        
        # Create dataframes with proper indices
        index = df_clean.index
        
        # Power transformed features (if applied)
        if X_power_transformed is not None:
            results['power_transformed'] = pd.DataFrame(
                X_power_transformed, 
                columns=numerical_features, 
                index=index
            )
        
        # Scaled features
        results['scaled'] = pd.DataFrame(
            X_scaled, 
            columns=numerical_features, 
            index=index
        )
        
        # Combined features (scaled + encoded categorical)
        results['combined'] = pd.DataFrame(
            X_combined, 
            columns=combined_feature_names, 
            index=index
        )
        
        # Categorical features (if any)
        if X_categorical.shape[1] > 0:
            results['categorical_encoded'] = pd.DataFrame(
                X_categorical, 
                columns=categorical_feature_names, 
                index=index
            )
        
        # Dimensionality reduction results
        for method, (X_reduced, reducer) in reduction_results.items():
            if method == 'pca':
                self.pca = reducer
                feature_names = [f'PCA_{i+1}' for i in range(X_reduced.shape[1])]
            elif method == 'tsne':
                self.tsne = reducer
                feature_names = [f't-SNE_{i+1}' for i in range(X_reduced.shape[1])]
            
            results[method] = pd.DataFrame(
                X_reduced, 
                columns=feature_names, 
                index=index
            )
        
        # Create complete dataset with original + processed features
        complete_data = df_clean.copy()
        
        # Add scaled features
        for col in results['scaled'].columns:
            complete_data[f'{col}_scaled'] = results['scaled'][col]
        
        # Add PCA features if available
        if 'pca' in results:
            for col in results['pca'].columns:
                complete_data[col] = results['pca'][col]
        
        # Add t-SNE features if available
        if 'tsne' in results:
            for col in results['tsne'].columns:
                complete_data[col] = results['tsne'][col]
        
        results['complete'] = complete_data
        
        # Store feature names and mark as fitted
        self.feature_names_ = {
            'numerical': numerical_features,
            'categorical': categorical_features,
            'categorical_encoded': categorical_feature_names,
            'combined': combined_feature_names
        }
        
        self.fitted = True
        
        self._log_step("Pipeline Fitting Complete", 
                      f"Generated {len(results)} dataset variants")
        
        return results
    
    def transform(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Transform new data using fitted pipeline.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dictionary containing transformed datasets
        """
        if not self.fitted:
            raise ValueError("Pipeline must be fitted before transforming new data")
        
        logger.info("Transforming new data using fitted pipeline")
        
        # Apply same preprocessing steps
        feature_types = self._identify_feature_types(df)
        df_clean = self._handle_missing_values(df, feature_types)
        
        # Transform numerical features
        numerical_features = self.feature_names_['numerical']
        X_numerical = df_clean[numerical_features].values
        
        # Apply power transformation if fitted
        if self.power_transformer is not None:
            X_numerical = self.power_transformer.transform(X_numerical)
        
        # Apply scaling
        X_scaled = self.scaler.transform(X_numerical)
        
        # Transform categorical features
        if self.categorical_encoder is not None:
            categorical_features = self.feature_names_['categorical']
            X_categorical = self.categorical_encoder.transform(df_clean[categorical_features])
            X_combined = np.hstack([X_scaled, X_categorical])
        else:
            X_categorical = np.array([]).reshape(len(df_clean), 0)
            X_combined = X_scaled
        
        # Apply dimensionality reduction
        results = {}
        index = df_clean.index
        
        # Scaled features
        results['scaled'] = pd.DataFrame(
            X_scaled, 
            columns=numerical_features, 
            index=index
        )
        
        # Combined features
        results['combined'] = pd.DataFrame(
            X_combined, 
            columns=self.feature_names_['combined'], 
            index=index
        )
        
        # PCA
        if self.pca is not None:
            X_pca = self.pca.transform(X_combined)
            results['pca'] = pd.DataFrame(
                X_pca, 
                columns=[f'PCA_{i+1}' for i in range(X_pca.shape[1])], 
                index=index
            )
        
        # t-SNE (Note: t-SNE doesn't have a transform method, would need to refit)
        # For new data, we typically don't apply t-SNE as it's primarily for visualization
        
        return results
    
    def save_pipeline(self, filepath: str) -> None:
        """Save the fitted pipeline to disk."""
        if not self.fitted:
            raise ValueError("Pipeline must be fitted before saving")
        
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Save pipeline components
        pipeline_data = {
            'config': self.config,
            'feature_names': self.feature_names_,
            'preprocessing_log': self.preprocessing_log,
            'fitted': self.fitted
        }
        
        # Save scikit-learn objects separately
        components_to_save = {
            'power_transformer': self.power_transformer,
            'scaler': self.scaler,
            'categorical_encoder': self.categorical_encoder,
            'pca': self.pca,
            'tsne': self.tsne
        }
        
        # Save main pipeline data
        joblib.dump(pipeline_data, f"{filepath}_pipeline.pkl")
        
        # Save components
        for name, component in components_to_save.items():
            if component is not None:
                joblib.dump(component, f"{filepath}_{name}.pkl")
        
        logger.info(f"Pipeline saved to {filepath}")
    
    def load_pipeline(self, filepath: str) -> None:
        """Load a fitted pipeline from disk."""
        try:
            # Load main pipeline data
            pipeline_data = joblib.load(f"{filepath}_pipeline.pkl")
            
            self.config = pipeline_data['config']
            self.feature_names_ = pipeline_data['feature_names']
            self.preprocessing_log = pipeline_data['preprocessing_log']
            self.fitted = pipeline_data['fitted']
            
            # Load components
            components_to_load = ['power_transformer', 'scaler', 'categorical_encoder', 'pca', 'tsne']
            
            for name in components_to_load:
                component_path = f"{filepath}_{name}.pkl"
                if Path(component_path).exists():
                    setattr(self, name, joblib.load(component_path))
                else:
                    setattr(self, name, None)
            
            logger.info(f"Pipeline loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load pipeline from {filepath}: {e}")
            raise
    
    def validate_output(self, results: Dict[str, pd.DataFrame]) -> Dict[str, bool]:
        """Validate preprocessing outputs."""
        validation_results = {}
        
        if not self.config['validation']['check_missing_values']:
            return validation_results
        
        # Check for missing values
        for dataset_name, dataset in results.items():
            if dataset_name in ['tsne']:  # Skip visualization datasets
                continue
                
            missing_values = dataset.isnull().sum().sum()
            validation_results[f"{dataset_name}_no_missing"] = missing_values == 0
            
            if missing_values > 0:
                logger.warning(f"Found {missing_values} missing values in {dataset_name}")
        
        # Check feature ranges for scaled data
        if 'scaled' in results and self.config['validation']['check_feature_ranges']:
            scaled_data = results['scaled']
            
            # For StandardScaler, mean should be ~0 and std should be ~1
            if isinstance(self.scaler, StandardScaler):
                means = scaled_data.mean()
                stds = scaled_data.std()
                
                mean_check = (abs(means) < 0.1).all()  # Allow small deviations
                std_check = (abs(stds - 1.0) < 0.1).all()
                
                validation_results['scaled_mean_centered'] = mean_check
                validation_results['scaled_unit_variance'] = std_check
        
        # Check shape consistency
        if self.config['validation']['check_shape_consistency']:
            base_shape = None
            for dataset_name, dataset in results.items():
                if base_shape is None:
                    base_shape = dataset.shape[0]
                
                shape_consistent = dataset.shape[0] == base_shape
                validation_results[f"{dataset_name}_shape_consistent"] = shape_consistent
        
        # Log validation results
        passed_checks = sum(validation_results.values())
        total_checks = len(validation_results)
        
        self._log_step("Validation Complete", 
                      f"Passed {passed_checks}/{total_checks} validation checks")
        
        return validation_results
    
    def get_preprocessing_summary(self) -> Dict:
        """Get a summary of preprocessing steps performed."""
        if not self.fitted:
            return {"error": "Pipeline not fitted"}
        
        summary = {
            'pipeline_fitted': self.fitted,
            'config_used': self.config,
            'feature_counts': {
                'numerical': len(self.feature_names_.get('numerical', [])),
                'categorical': len(self.feature_names_.get('categorical', [])),
                'categorical_encoded': len(self.feature_names_.get('categorical_encoded', [])),
                'combined': len(self.feature_names_.get('combined', []))
            },
            'transformations_applied': {
                'power_transformation': self.power_transformer is not None,
                'scaling': self.scaler is not None,
                'categorical_encoding': self.categorical_encoder is not None,
                'pca': self.pca is not None,
                'tsne': self.tsne is not None
            },
            'preprocessing_log': self.preprocessing_log
        }
        
        return summary


def create_config_file(filepath: str, config_type: str = 'yaml') -> None:
    """
    Create a sample configuration file for the preprocessing pipeline.
    
    Args:
        filepath: Path where to save the configuration file
        config_type: Type of config file ('yaml' or 'json')
    """
    sample_config = {
        'preprocessing': {
            'missing_strategy_numerical': 'median',
            'missing_strategy_categorical': 'most_frequent',
            'scaling_method': 'standard',
            'apply_power_transform': True,
            'power_transform_method': 'yeo-johnson',
            'skewness_threshold': 1.0,
            'categorical_encoding': 'onehot',
            'drop_first_category': True
        },
        'dimensionality_reduction': {
            'apply_pca': True,
            'pca_n_components': 0.95,
            'pca_min_components': 5,
            'apply_tsne': True,
            'tsne_n_components': 2,
            'tsne_perplexity': 30,
            'tsne_random_state': 42
        },
        'feature_categories': {
            'financial_features': ['Revenue', 'ProfitMargin', 'MarketCap', 'GrowthRate'],
            'esg_features': ['ESG_Overall', 'ESG_Environmental', 'ESG_Social', 'ESG_Governance'],
            'environmental_features': ['CarbonEmissions', 'WaterUsage', 'EnergyConsumption'],
            'categorical_features': ['Industry', 'Region'],
            'identifier_features': ['CompanyID', 'CompanyName', 'Year']
        },
        'validation': {
            'check_missing_values': True,
            'check_feature_ranges': True,
            'check_shape_consistency': True,
            'log_transformations': True
        },
        'output': {
            'save_intermediate_steps': True,
            'save_path': '../Data/',
            'save_fitted_pipeline': True,
            'pipeline_save_path': '../Models/'
        }
    }
    
    # Ensure directory exists
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    if config_type.lower() == 'yaml':
        with open(filepath, 'w') as f:
            yaml.dump(sample_config, f, default_flow_style=False, indent=2)
    else:
        with open(filepath, 'w') as f:
            json.dump(sample_config, f, indent=2)
    
    print(f"Sample configuration saved to {filepath}")


def run_pipeline_example(data_path: str, config_path: Optional[str] = None) -> None:
    """
    Example usage of the preprocessing pipeline.
    
    Args:
        data_path: Path to the input data file
        config_path: Path to configuration file (optional)
    """
    # Load data
    print(f"Loading data from {data_path}")
    data = pd.read_csv(data_path)
    print(f"Data shape: {data.shape}")
    
    # Initialize pipeline
    pipeline = ESGPreprocessingPipeline(config_path)
    
    # Fit and transform data
    print("Fitting and transforming data...")
    results = pipeline.fit_transform(data)
    
    # Print results summary
    print("\nPreprocessing Results:")
    for dataset_name, dataset in results.items():
        print(f"  {dataset_name}: {dataset.shape}")
    
    # Validate outputs
    validation_results = pipeline.validate_output(results)
    print(f"\nValidation Results: {validation_results}")
    
    # Get summary
    summary = pipeline.get_preprocessing_summary()
    print(f"\nTransformations applied:")
    for transform, applied in summary['transformations_applied'].items():
        print(f"  {transform}: {'✓' if applied else '✗'}")
    
    # Save pipeline
    models_dir = Path('../Models')
    models_dir.mkdir(exist_ok=True)
    pipeline.save_pipeline('../Models/esg_preprocessing_pipeline')
    
    # Save processed datasets
    data_dir = Path('../Data')
    data_dir.mkdir(exist_ok=True)
    
    for dataset_name, dataset in results.items():
        if dataset_name != 'complete':  # Save main datasets separately
            output_path = data_dir / f"{dataset_name}_features.csv"
            dataset.to_csv(output_path, index=False)
            print(f"Saved {dataset_name} features to {output_path}")
    
    # Save complete dataset
    results['complete'].to_csv(data_dir / 'preprocessed_complete_dataset.csv', index=False)
    print(f"Saved complete dataset to {data_dir / 'preprocessed_complete_dataset.csv'}")


if __name__ == "__main__":
    # Create sample configuration file
    create_config_file('preprocessing_config.yaml', 'yaml')
    
    # Example usage (uncomment to run)
    # run_pipeline_example('../Data/company_esg_financial_dataset.csv', 'preprocessing_config.yaml')
