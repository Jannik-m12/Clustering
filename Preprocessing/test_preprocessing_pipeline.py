"""
Test Suite for ESG Preprocessing Pipeline

This module contains comprehensive tests for the preprocessing pipeline,
ensuring data quality, transformation consistency, and reproducibility.
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the preprocessing module to the path
sys.path.append(os.path.dirname(__file__))

from preprocessing_pipeline import ESGPreprocessingPipeline, create_config_file


class TestESGPreprocessingPipeline:
    """Test suite for ESG Preprocessing Pipeline."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample ESG data for testing."""
        np.random.seed(42)
        n_samples = 1000
        
        data = {
            'CompanyID': range(1, n_samples + 1),
            'CompanyName': [f'Company_{i}' for i in range(1, n_samples + 1)],
            'Industry': np.random.choice(['Technology', 'Finance', 'Energy', 'Healthcare'], n_samples),
            'Region': np.random.choice(['North America', 'Europe', 'Asia', 'Latin America'], n_samples),
            'Year': np.random.choice([2020, 2021, 2022, 2023], n_samples),
            'Revenue': np.random.lognormal(6, 1, n_samples),  # Log-normal for realistic skew
            'ProfitMargin': np.random.normal(10, 5, n_samples),
            'MarketCap': np.random.lognormal(8, 1.5, n_samples),
            'GrowthRate': np.random.normal(5, 10, n_samples),
            'ESG_Overall': np.random.uniform(20, 90, n_samples),
            'ESG_Environmental': np.random.uniform(10, 95, n_samples),
            'ESG_Social': np.random.uniform(15, 85, n_samples),
            'ESG_Governance': np.random.uniform(25, 95, n_samples),
            'CarbonEmissions': np.random.lognormal(10, 2, n_samples),
            'WaterUsage': np.random.lognormal(8, 1.5, n_samples),
            'EnergyConsumption': np.random.lognormal(12, 2, n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Introduce some missing values
        missing_indices = np.random.choice(df.index, size=50, replace=False)
        df.loc[missing_indices[:25], 'Revenue'] = np.nan
        df.loc[missing_indices[25:], 'Industry'] = np.nan
        
        return df
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration file."""
        temp_dir = tempfile.mkdtemp()
        config_path = Path(temp_dir) / 'test_config.yaml'
        create_config_file(str(config_path), 'yaml')
        
        yield str(config_path)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_pipeline_initialization(self, temp_config):
        """Test pipeline initialization with and without config."""
        # Test with config file
        pipeline_with_config = ESGPreprocessingPipeline(temp_config)
        assert pipeline_with_config.config is not None
        assert not pipeline_with_config.fitted
        
        # Test without config file (default config)
        pipeline_default = ESGPreprocessingPipeline()
        assert pipeline_default.config is not None
        assert not pipeline_default.fitted
    
    def test_feature_type_identification(self, sample_data):
        """Test automatic feature type identification."""
        pipeline = ESGPreprocessingPipeline()
        feature_types = pipeline._identify_feature_types(sample_data)
        
        assert 'numerical_features' in feature_types
        assert 'categorical_features_available' in feature_types
        assert len(feature_types['numerical_features']) > 0
        assert len(feature_types['categorical_features_available']) > 0
        
        # Check specific features
        assert 'Revenue' in feature_types['numerical_features']
        assert 'Industry' in feature_types['categorical_features_available']
    
    def test_missing_value_handling(self, sample_data):
        """Test missing value imputation."""
        pipeline = ESGPreprocessingPipeline()
        feature_types = pipeline._identify_feature_types(sample_data)
        
        # Verify missing values exist
        assert sample_data.isnull().sum().sum() > 0
        
        # Handle missing values
        df_clean = pipeline._handle_missing_values(sample_data, feature_types)
        
        # Verify no missing values remain
        assert df_clean.isnull().sum().sum() == 0
    
    def test_power_transformation(self, sample_data):
        """Test power transformation for skewness reduction."""
        pipeline = ESGPreprocessingPipeline()
        
        # Get numerical features
        numerical_features = ['Revenue', 'MarketCap', 'CarbonEmissions']
        X = sample_data[numerical_features].dropna().values
        
        # Apply power transformation
        X_transformed, transformer = pipeline._apply_power_transformation(X, numerical_features)
        
        if transformer is not None:
            # Check that transformation was applied
            assert X_transformed is not None
            assert X_transformed.shape == X.shape
            
            # Check that skewness was reduced for highly skewed features
            from scipy.stats import skew
            for i, feature in enumerate(numerical_features):
                original_skew = abs(skew(X[:, i]))
                transformed_skew = abs(skew(X_transformed[:, i]))
                
                if original_skew >= 1.0:  # Only check highly skewed features
                    assert transformed_skew <= original_skew  # Should be reduced or same
    
    def test_scaling(self, sample_data):
        """Test feature scaling."""
        pipeline = ESGPreprocessingPipeline()
        
        # Get numerical data
        numerical_features = ['Revenue', 'ProfitMargin', 'MarketCap']
        X = sample_data[numerical_features].dropna().values
        
        # Apply scaling
        X_scaled, scaler = pipeline._apply_scaling(X)
        
        assert X_scaled.shape == X.shape
        assert scaler is not None
        
        # For StandardScaler, check mean ~0 and std ~1
        if hasattr(scaler, 'mean_'):
            assert np.allclose(X_scaled.mean(axis=0), 0, atol=1e-10)
            assert np.allclose(X_scaled.std(axis=0), 1, atol=1e-10)
    
    def test_categorical_encoding(self, sample_data):
        """Test categorical feature encoding."""
        pipeline = ESGPreprocessingPipeline()
        
        categorical_features = ['Industry', 'Region']
        X_categorical, feature_names, encoder = pipeline._encode_categorical_features(
            sample_data, categorical_features
        )
        
        assert encoder is not None
        assert len(feature_names) > 0
        assert X_categorical.shape[0] == len(sample_data)
        assert X_categorical.shape[1] == len(feature_names)
    
    def test_fit_transform(self, sample_data):
        """Test complete fit_transform pipeline."""
        pipeline = ESGPreprocessingPipeline()
        
        # Fit and transform
        results = pipeline.fit_transform(sample_data)
        
        # Check that pipeline is fitted
        assert pipeline.fitted
        
        # Check that required datasets are created
        assert 'scaled' in results
        assert 'combined' in results
        assert 'complete' in results
        
        # Check shapes
        n_samples = len(sample_data)
        for dataset_name, dataset in results.items():
            assert len(dataset) == n_samples
            assert isinstance(dataset, pd.DataFrame)
    
    def test_transform_new_data(self, sample_data):
        """Test transforming new data with fitted pipeline."""
        pipeline = ESGPreprocessingPipeline()
        
        # Split data
        train_data = sample_data.iloc[:800].copy()
        test_data = sample_data.iloc[800:].copy()
        
        # Fit on training data
        pipeline.fit_transform(train_data)
        
        # Transform test data
        test_results = pipeline.transform(test_data)
        
        # Check that results have correct shapes
        assert 'scaled' in test_results
        assert len(test_results['scaled']) == len(test_data)
    
    def test_pipeline_persistence(self, sample_data, temp_config):
        """Test saving and loading pipeline."""
        pipeline1 = ESGPreprocessingPipeline(temp_config)
        
        # Fit pipeline
        results1 = pipeline1.fit_transform(sample_data)
        
        # Save pipeline
        temp_dir = tempfile.mkdtemp()
        pipeline_path = Path(temp_dir) / 'test_pipeline'
        pipeline1.save_pipeline(str(pipeline_path))
        
        # Load pipeline
        pipeline2 = ESGPreprocessingPipeline()
        pipeline2.load_pipeline(str(pipeline_path))
        
        # Check that loaded pipeline is fitted
        assert pipeline2.fitted
        
        # Transform new data with loaded pipeline
        test_data = sample_data.iloc[:100].copy()
        results2 = pipeline2.transform(test_data)
        
        # Check that results have correct structure
        assert 'scaled' in results2
        assert len(results2['scaled']) == len(test_data)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_validation(self, sample_data):
        """Test pipeline validation."""
        pipeline = ESGPreprocessingPipeline()
        
        # Fit and transform
        results = pipeline.fit_transform(sample_data)
        
        # Validate results
        validation_results = pipeline.validate_output(results)
        
        assert isinstance(validation_results, dict)
        assert len(validation_results) > 0
        
        # Check that most validations pass
        passed_validations = sum(validation_results.values())
        total_validations = len(validation_results)
        pass_rate = passed_validations / total_validations
        
        assert pass_rate >= 0.8  # At least 80% of validations should pass
    
    def test_preprocessing_summary(self, sample_data):
        """Test preprocessing summary generation."""
        pipeline = ESGPreprocessingPipeline()
        
        # Before fitting
        summary_before = pipeline.get_preprocessing_summary()
        assert 'error' in summary_before
        
        # After fitting
        pipeline.fit_transform(sample_data)
        summary_after = pipeline.get_preprocessing_summary()
        
        assert 'pipeline_fitted' in summary_after
        assert summary_after['pipeline_fitted'] is True
        assert 'feature_counts' in summary_after
        assert 'transformations_applied' in summary_after
        assert 'preprocessing_log' in summary_after
    
    def test_config_creation(self):
        """Test configuration file creation."""
        temp_dir = tempfile.mkdtemp()
        
        # Test YAML config
        yaml_path = Path(temp_dir) / 'test_config.yaml'
        create_config_file(str(yaml_path), 'yaml')
        assert yaml_path.exists()
        
        # Test JSON config
        json_path = Path(temp_dir) / 'test_config.json'
        create_config_file(str(json_path), 'json')
        assert json_path.exists()
        
        # Cleanup
        shutil.rmtree(temp_dir)


def run_manual_tests():
    """Run manual tests for visual inspection."""
    print("Running manual tests...")
    
    # Create sample data
    np.random.seed(42)
    n_samples = 500
    
    data = {
        'CompanyID': range(1, n_samples + 1),
        'CompanyName': [f'Company_{i}' for i in range(1, n_samples + 1)],
        'Industry': np.random.choice(['Technology', 'Finance', 'Energy'], n_samples),
        'Region': np.random.choice(['North America', 'Europe', 'Asia'], n_samples),
        'Year': np.random.choice([2022, 2023], n_samples),
        'Revenue': np.random.lognormal(6, 1, n_samples),
        'ProfitMargin': np.random.normal(10, 5, n_samples),
        'MarketCap': np.random.lognormal(8, 1.5, n_samples),
        'GrowthRate': np.random.normal(5, 10, n_samples),
        'ESG_Overall': np.random.uniform(20, 90, n_samples),
        'ESG_Environmental': np.random.uniform(10, 95, n_samples),
        'ESG_Social': np.random.uniform(15, 85, n_samples),
        'ESG_Governance': np.random.uniform(25, 95, n_samples),
        'CarbonEmissions': np.random.lognormal(10, 2, n_samples),
        'WaterUsage': np.random.lognormal(8, 1.5, n_samples),
        'EnergyConsumption': np.random.lognormal(12, 2, n_samples)
    }
    
    df = pd.DataFrame(data)
    print(f"Created sample data: {df.shape}")
    
    # Test pipeline
    pipeline = ESGPreprocessingPipeline()
    print("Initialized pipeline")
    
    results = pipeline.fit_transform(df)
    print(f"Fit and transformed data")
    
    # Print results
    print("\nResults summary:")
    for dataset_name, dataset in results.items():
        print(f"  {dataset_name}: {dataset.shape}")
    
    # Validation
    validation_results = pipeline.validate_output(results)
    print(f"\nValidation results:")
    for check, passed in validation_results.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    
    # Summary
    summary = pipeline.get_preprocessing_summary()
    print(f"\nTransformations applied:")
    for transform, applied in summary['transformations_applied'].items():
        status = "✓" if applied else "✗"
        print(f"  {status} {transform}")
    
    print("\nManual tests completed successfully!")


if __name__ == "__main__":
    run_manual_tests()