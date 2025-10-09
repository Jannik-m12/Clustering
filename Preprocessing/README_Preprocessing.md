# ESG Preprocessing Pipeline

## Overview

This repository contains a comprehensive, reproducible preprocessing pipeline designed for ESG (Environmental, Social, Governance) financial clustering analysis. The pipeline implements industry best practices for data preparation, ensuring consistent, auditable, and reproducible results across different datasets and computing environments.

## 🎯 Key Features

### **Reproducibility & Consistency**
- ✅ **Deterministic Results**: Same outputs across runs and environments
- ✅ **Version Control**: All preprocessing parameters tracked and saved
- ✅ **Serializable Pipeline**: Save/load fitted transformers for production use
- ✅ **Docker Support**: Containerized environment for deployment

### **Modular Architecture**
- ✅ **Configurable Parameters**: External YAML/JSON configuration files
- ✅ **Automated Testing**: Comprehensive test suite with validation checks
- ✅ **Logging**: Detailed transformation logs for audit trails
- ✅ **Error Handling**: Robust error detection and reporting

### **Advanced Preprocessing**
- ✅ **Smart Missing Value Handling**: Configurable strategies for different data types
- ✅ **Skewness Correction**: Power transformations (Yeo-Johnson, Box-Cox)
- ✅ **Multiple Scaling Methods**: Standard, Robust, MinMax scaling options
- ✅ **Categorical Encoding**: One-hot encoding with multicollinearity handling
- ✅ **Dimensionality Reduction**: PCA and t-SNE with optimal component selection

### **Quality Assurance**
- ✅ **Automated Validation**: Data quality checks and range validation
- ✅ **Pipeline Testing**: Consistency tests across different datasets
- ✅ **Color-Blind Friendly**: Accessible visualization color schemes
- ✅ **Business Context**: ESG-specific feature categorization

## 📁 Project Structure

```
Preprocessing/
├── preprocessing_pipeline.py      # Main pipeline implementation
├── preprocessing_config.yaml      # Configuration file
├── test_preprocessing_pipeline.py # Comprehensive test suite
├── run_pipeline.sh               # Automated execution script
├── Dockerfile                    # Container configuration
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd Clustering-ESG-Financial-Performance/Preprocessing

# Install dependencies
pip install -r requirements.txt
```

### 2. Basic Usage

```python
from preprocessing_pipeline import ESGPreprocessingPipeline
import pandas as pd

# Load your data
data = pd.read_csv('../Data/company_esg_financial_dataset.csv')

# Initialize pipeline
pipeline = ESGPreprocessingPipeline('preprocessing_config.yaml')

# Fit and transform data
results = pipeline.fit_transform(data)

# Access different dataset versions
scaled_features = results['scaled']          # Scaled numerical features
pca_features = results['pca']               # PCA-reduced features
complete_dataset = results['complete']       # Full dataset with all transformations
```

### 3. Automated Execution

```bash
# Run the complete pipeline
./run_pipeline.sh

# Run with tests
./run_pipeline.sh --test
```

## ⚙️ Configuration

The pipeline is highly configurable through the `preprocessing_config.yaml` file:

```yaml
preprocessing:
  missing_strategy_numerical: 'median'
  scaling_method: 'standard'
  apply_power_transform: true
  skewness_threshold: 1.0

dimensionality_reduction:
  apply_pca: true
  pca_n_components: 0.95  # 95% explained variance
  apply_tsne: true

feature_categories:
  financial_features: ['Revenue', 'ProfitMargin', 'MarketCap', 'GrowthRate']
  esg_features: ['ESG_Overall', 'ESG_Environmental', 'ESG_Social', 'ESG_Governance']
  environmental_features: ['CarbonEmissions', 'WaterUsage', 'EnergyConsumption']
  categorical_features: ['Industry', 'Region']
```

## 📊 Pipeline Steps

### 1. **Data Loading & Validation**
- Automatic feature type detection
- Data quality assessment
- Missing value analysis

### 2. **Missing Value Handling**
- Numerical: Median/Mean/Mode imputation
- Categorical: Most frequent/Constant imputation
- Configurable strategies per feature type

### 3. **Skewness Correction**
- Automatic skewness detection
- Power transformations (Yeo-Johnson/Box-Cox)
- Pre/post transformation comparison

### 4. **Feature Scaling**
- StandardScaler (mean=0, std=1)
- RobustScaler (median=0, IQR=1)
- MinMaxScaler (min=0, max=1)

### 5. **Categorical Encoding**
- One-hot encoding with optional first category drop
- Multicollinearity prevention
- Unknown category handling

### 6. **Dimensionality Reduction**
- PCA with explained variance optimization
- t-SNE for visualization
- Automatic component selection

### 7. **Quality Validation**
- Missing value checks
- Feature range validation
- Shape consistency verification
- Statistical property validation

## 🧪 Testing

The pipeline includes comprehensive tests:

```bash
# Run manual tests
python test_preprocessing_pipeline.py

# Run with pytest (if installed)
pytest test_preprocessing_pipeline.py -v

# Test specific functionality
python -c "from test_preprocessing_pipeline import TestESGPreprocessingPipeline; t = TestESGPreprocessingPipeline(); t.test_fit_transform(t.sample_data())"
```

## 🐳 Docker Usage

```bash
# Build container
docker build -t esg-preprocessing .

# Run pipeline in container
docker run -v $(PWD)/../Data:/app/Data -v $(PWD)/../Models:/app/Models esg-preprocessing

# Interactive development
docker run -it -v $(PWD):/app esg-preprocessing bash
```

## 📈 Output Datasets

The pipeline generates multiple dataset versions:

| Dataset | Description | Use Case |
|---------|-------------|----------|
| `scaled` | Scaled numerical features | Standard clustering algorithms |
| `combined` | Scaled + encoded categorical | Enhanced clustering with context |
| `pca` | PCA-reduced features | High-dimensional clustering |
| `tsne` | 2D visualization features | Data exploration and plotting |
| `complete` | Original + all transformations | Comprehensive analysis |

## 🎨 Color-Blind Friendly Visualizations

The pipeline includes Paul Tol's scientifically-backed color scheme for accessibility:

```python
CLUSTER_COLORS = {
    0: '#4477AA',  # Blue - universally distinguishable
    1: '#EE6677',  # Rose - distinct from blue
    2: '#228833',  # Green - colorblind-safe
    3: '#CCBB44',  # Yellow - high contrast
    4: '#66CCEE',  # Cyan - distinct from blue/green
    5: '#AA3377',  # Purple - strong contrast
    6: '#BBBBBB',  # Gray - neutral
}
```

## 📋 Requirements

### Python Dependencies
- `pandas >= 1.5.0`
- `numpy >= 1.21.0`
- `scikit-learn >= 1.1.0`
- `scipy >= 1.9.0`
- `PyYAML >= 6.0`
- `joblib >= 1.2.0`

### System Requirements
- Python 3.8+
- 4GB RAM minimum (8GB recommended for large datasets)
- Docker (optional, for containerized deployment)

## 🔧 Advanced Usage

### Custom Configuration

```python
# Create custom config
config = {
    'preprocessing': {
        'scaling_method': 'robust',
        'apply_power_transform': False
    },
    'dimensionality_reduction': {
        'pca_n_components': 10  # Explicit number
    }
}

# Initialize with custom config
pipeline = ESGPreprocessingPipeline()
pipeline.config = config
```

### Pipeline Persistence

```python
# Save fitted pipeline
pipeline.save_pipeline('../Models/my_pipeline')

# Load and use
new_pipeline = ESGPreprocessingPipeline()
new_pipeline.load_pipeline('../Models/my_pipeline')

# Transform new data
new_results = new_pipeline.transform(new_data)
```

### Validation and Monitoring

```python
# Get detailed summary
summary = pipeline.get_preprocessing_summary()
print(f"Transformations applied: {summary['transformations_applied']}")

# Validate outputs
validation_results = pipeline.validate_output(results)
print(f"Validation checks passed: {sum(validation_results.values())}/{len(validation_results)}")
```

## 🐛 Troubleshooting

### Common Issues

**1. Memory Issues with Large Datasets**
```python
# Reduce t-SNE samples or disable
config['dimensionality_reduction']['apply_tsne'] = False
```

**2. Categorical Encoding Explosion**
```python
# Limit categorical features or use different encoding
config['preprocessing']['categorical_encoding'] = 'label'
```

**3. PCA Component Selection**
```python
# Use explicit number instead of variance threshold
config['dimensionality_reduction']['pca_n_components'] = 20
```

## 📚 Documentation

### API Reference

#### `ESGPreprocessingPipeline`

**Methods:**
- `fit_transform(df)`: Fit pipeline and transform data
- `transform(df)`: Transform new data with fitted pipeline
- `save_pipeline(path)`: Save fitted pipeline to disk
- `load_pipeline(path)`: Load fitted pipeline from disk
- `validate_output(results)`: Validate preprocessing results
- `get_preprocessing_summary()`: Get detailed processing summary

**Configuration Options:**
- `missing_strategy_numerical`: 'median', 'mean', 'mode'
- `scaling_method`: 'standard', 'robust', 'minmax'  
- `power_transform_method`: 'yeo-johnson', 'box-cox'
- `categorical_encoding`: 'onehot', 'label'

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python test_preprocessing_pipeline.py`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Paul Tol** for the color-blind friendly color schemes
- **scikit-learn** team for robust preprocessing tools
- **ESG Research Community** for domain expertise and validation

---

## 🎯 Business Impact

This preprocessing pipeline ensures that ESG clustering analysis is:

- **✅ Reproducible**: Results can be replicated for regulatory compliance
- **✅ Scalable**: Handles datasets from thousands to millions of records  
- **✅ Accessible**: Color-blind friendly visualizations for all stakeholders
- **✅ Auditable**: Complete transformation logs for transparency
- **✅ Production-Ready**: Containerized deployment with automated testing

Perfect for sustainability reporting, ESG investment analysis, and regulatory compliance! 🌱📊