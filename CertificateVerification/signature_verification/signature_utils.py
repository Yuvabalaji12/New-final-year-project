"""
Signature Verification Utilities
Preprocessing, image handling, and performance metric generation
for deep learning-based signature verification.
"""

import numpy as np
from PIL import Image, ImageOps
import io
import os


# Target image size for the Siamese Network input
IMG_SIZE = (105, 105)


def preprocess_signature(image_input):
    """
    Preprocess a signature image for the Siamese Neural Network.
    
    Accepts:
        - A file path (str)
        - A PIL Image object
        - A bytes/BytesIO object (from Flask file upload)
    
    Returns:
        numpy array of shape (1, 105, 105, 1) normalized to [0, 1]
    """
    if isinstance(image_input, str):
        # File path
        img = Image.open(image_input)
    elif isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, io.BytesIO):
        img = Image.open(image_input)
    elif isinstance(image_input, Image.Image):
        img = image_input
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")
    
    # Convert to grayscale
    img = ImageOps.grayscale(img)
    
    # Resize to target dimensions
    img = img.resize(IMG_SIZE, Image.LANCZOS)
    
    # Convert to numpy array and normalize to [0, 1]
    img_array = np.array(img, dtype=np.float32) / 255.0
    
    # Reshape to (1, 105, 105, 1) for model input
    img_array = img_array.reshape(1, IMG_SIZE[0], IMG_SIZE[1], 1)
    
    return img_array


def save_uploaded_signature(file_storage, save_path):
    """
    Save a Flask FileStorage object as a signature image.
    Converts to grayscale PNG for consistency.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    img = Image.open(file_storage)
    img = ImageOps.grayscale(img)
    img.save(save_path, 'PNG')
    return save_path


def generate_performance_metrics(predictions, true_labels):
    """
    Generate performance metrics for signature verification.
    
    Args:
        predictions: list of predicted labels (0 = forged, 1 = genuine)
        true_labels: list of true labels (0 = forged, 1 = genuine)
    
    Returns:
        dict with accuracy, precision, recall, f1_score
    """
    predictions = np.array(predictions)
    true_labels = np.array(true_labels)
    
    # True Positives, False Positives, True Negatives, False Negatives
    tp = np.sum((predictions == 1) & (true_labels == 1))
    fp = np.sum((predictions == 1) & (true_labels == 0))
    tn = np.sum((predictions == 0) & (true_labels == 0))
    fn = np.sum((predictions == 0) & (true_labels == 1))
    
    accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'accuracy': round(accuracy * 100, 2),
        'precision': round(precision * 100, 2),
        'recall': round(recall * 100, 2),
        'f1_score': round(f1_score * 100, 2),
        'true_positives': int(tp),
        'false_positives': int(fp),
        'true_negatives': int(tn),
        'false_negatives': int(fn),
        'total_samples': len(true_labels)
    }


def generate_demo_metrics():
    """
    Generate realistic demo performance metrics for the analytics dashboard.
    Simulates results from testing a Siamese Network on signature datasets.
    """
    # Simulated results from different deep learning techniques
    techniques = {
        'Siamese Neural Network (CNN)': {
            'accuracy': 96.8,
            'precision': 97.2,
            'recall': 96.1,
            'f1_score': 96.6,
            'training_time': '45 min',
            'params': '1.2M'
        },
        'VGG-16 Transfer Learning': {
            'accuracy': 94.3,
            'precision': 95.0,
            'recall': 93.5,
            'f1_score': 94.2,
            'training_time': '120 min',
            'params': '138M'
        },
        'ResNet-50 Fine-tuned': {
            'accuracy': 95.1,
            'precision': 95.8,
            'recall': 94.3,
            'f1_score': 95.0,
            'training_time': '90 min',
            'params': '25.6M'
        },
        'Basic CNN': {
            'accuracy': 89.7,
            'precision': 90.5,
            'recall': 88.9,
            'f1_score': 89.7,
            'training_time': '20 min',
            'params': '0.5M'
        },
        'SVM + HOG Features': {
            'accuracy': 82.4,
            'precision': 83.1,
            'recall': 81.6,
            'f1_score': 82.3,
            'training_time': '5 min',
            'params': 'N/A'
        }
    }
    
    # Epoch-wise training data for Siamese Network
    training_history = {
        'epochs': list(range(1, 26)),
        'train_accuracy': [
            52.1, 58.3, 64.7, 70.2, 75.8, 79.3, 82.6, 85.1, 87.3, 89.0,
            90.5, 91.8, 92.7, 93.4, 94.0, 94.5, 95.0, 95.4, 95.8, 96.1,
            96.3, 96.5, 96.6, 96.7, 96.8
        ],
        'val_accuracy': [
            50.3, 55.7, 61.2, 67.8, 72.3, 76.1, 79.4, 82.0, 84.5, 86.3,
            88.0, 89.5, 90.7, 91.6, 92.4, 93.0, 93.5, 94.0, 94.4, 94.8,
            95.1, 95.4, 95.6, 95.8, 96.0
        ],
        'train_loss': [
            0.693, 0.621, 0.548, 0.472, 0.401, 0.345, 0.298, 0.261, 0.230, 0.204,
            0.183, 0.165, 0.150, 0.137, 0.126, 0.117, 0.109, 0.102, 0.096, 0.091,
            0.087, 0.083, 0.080, 0.078, 0.076
        ],
        'val_loss': [
            0.700, 0.638, 0.572, 0.503, 0.438, 0.382, 0.335, 0.297, 0.266, 0.241,
            0.220, 0.203, 0.189, 0.177, 0.167, 0.159, 0.152, 0.146, 0.141, 0.137,
            0.133, 0.130, 0.128, 0.126, 0.124
        ]
    }
    
    return {
        'techniques': techniques,
        'training_history': training_history,
        'best_model': 'Siamese Neural Network (CNN)',
        'dataset_info': {
            'name': 'CEDAR Signature Dataset',
            'total_signatures': 2640,
            'genuine_pairs': 1320,
            'forged_pairs': 1320,
            'train_split': '80%',
            'test_split': '20%'
        }
    }
