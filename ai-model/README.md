# Waste Classification AI Model Training

## Overview
This directory contains the machine learning models for waste classification.

## Models Available

### 1. PyTorch Implementation (waste_classifier.py)
- **Architecture**: MobileNetV2 (Transfer Learning)
- **Input**: 224x224 RGB Images
- **Output**: 4 Classes (Plastic, Paper, Metal, Organic)
- **Features**:
  - Pre-trained weights
  - Data augmentation
  - Efficient inference

### 2. TensorFlow/Keras Implementation (tensorflow_classifier.py)
- **Architecture**: Custom CNN
- **Input**: 224x224 RGB Images
- **Output**: 4 Classes
- **Features**:
  - Easy to understand
  - Compatible with mobile deployment
  - GPU support

## Dataset Structure

Organize your training data as follows:

```
data/
├── plastic/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── paper/
│   ├── image1.jpg
│   └── ...
├── metal/
│   └── ...
└── organic/
    └── ...
```

## Training

### Using PyTorch:
```python
from waste_classifier import train_model
model = train_model("./data", epochs=20, batch_size=32)
```

### Using TensorFlow:
```python
from tensorflow_classifier import TensorFlowWasteClassifier
classifier = TensorFlowWasteClassifier()
classifier.train("./data", epochs=20, batch_size=32)
```

## Inference

### PyTorch:
```python
from waste_classifier import load_model, predict
model = load_model("waste_classifier.pth")
waste_type, confidence = predict(model, "image.jpg")
```

### TensorFlow:
```python
from tensorflow_classifier import TensorFlowWasteClassifier
classifier = TensorFlowWasteClassifier()
classifier.load_model("waste_classifier_tf.h5")
waste_type, confidence = classifier.predict("image.jpg")
```

## Performance Metrics
- Expected Accuracy: 90%+
- Inference Time: <100ms per image
- Model Size: ~10-50MB

## Requirements
- Python 3.8+
- torch/torchvision OR tensorflow/keras
- pillow
- numpy

## Notes
- Both models use transfer learning for better accuracy with less training data
- Data augmentation helps improve generalization
- Models are optimized for mobile deployment
