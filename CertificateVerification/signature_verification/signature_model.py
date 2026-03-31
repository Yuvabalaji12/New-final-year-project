"""
Signature Verification using Siamese Neural Network

Implements a deep learning-based signature verification system using
a Siamese Network architecture. The model takes two signature images
and determines whether they belong to the same person (genuine) or
if the test signature is a forgery.

Architecture:
    - Two identical CNN branches (shared weights)
    - Each branch: Conv2D → ReLU → MaxPool → Conv2D → ReLU → MaxPool → Flatten → Dense
    - L1 distance layer to compute absolute difference between feature vectors
    - Final sigmoid output: 1.0 = genuine match, 0.0 = forged

Reference: "Siamese Neural Networks for One-shot Image Recognition" (Koch et al., 2015)
"""

import numpy as np
import os

# Defer heavy imports to avoid slow startup when not needed
_tf = None
_layers = None
_Model = None


def _lazy_import_tf():
    """Lazily import TensorFlow to avoid slow startup."""
    global _tf, _layers, _Model
    if _tf is None:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF warnings
        import tensorflow as tf
        from tensorflow.keras import layers, Model
        _tf = tf
        _layers = layers
        _Model = Model
    return _tf, _layers, _Model


def _build_feature_extractor(input_shape=(105, 105, 1)):
    """
    Build the shared CNN feature extractor branch.
    
    Architecture follows a simplified version of the Siamese Network
    proposed for signature verification tasks.
    """
    tf, layers, Model = _lazy_import_tf()
    
    inp = layers.Input(shape=input_shape)
    
    # Block 1: 64 filters, 10x10 kernel
    x = layers.Conv2D(64, (10, 10), activation='relu', 
                      kernel_initializer='he_normal',
                      name='conv1')(inp)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Dropout(0.25)(x)
    
    # Block 2: 128 filters, 7x7 kernel
    x = layers.Conv2D(128, (7, 7), activation='relu',
                      kernel_initializer='he_normal',
                      name='conv2')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Dropout(0.25)(x)
    
    # Block 3: 128 filters, 4x4 kernel
    x = layers.Conv2D(128, (4, 4), activation='relu',
                      kernel_initializer='he_normal',
                      name='conv3')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Dropout(0.25)(x)
    
    # Block 4: 256 filters, 4x4 kernel
    x = layers.Conv2D(256, (4, 4), activation='relu',
                      kernel_initializer='he_normal',
                      name='conv4')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Flatten()(x)
    
    # Dense embedding layer
    x = layers.Dense(4096, activation='sigmoid',
                     kernel_initializer='he_normal')(x)
    
    return Model(inputs=inp, outputs=x, name='feature_extractor')

def _get_l1_layer():
    tf, layers, _ = _lazy_import_tf()
    
    @tf.keras.utils.register_keras_serializable(package='Custom')
    class L1DistanceLayer(layers.Layer):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            
        def call(self, inputs):
            return tf.abs(inputs[0] - inputs[1])
            
        def compute_output_shape(self, input_shape):
            return input_shape[0]
            
    return L1DistanceLayer



def build_siamese_model(input_shape=(105, 105, 1)):
    """
    Build the complete Siamese Neural Network for signature verification.
    
    Two input images are processed through the same CNN (shared weights).
    The L1 distance between their feature vectors is computed and passed
    through a sigmoid layer to produce the final similarity score.
    
    Returns:
        tf.keras.Model with two inputs and one output (similarity score)
    """
    tf, layers, Model = _lazy_import_tf()
    
    # Two input branches
    input_a = layers.Input(shape=input_shape, name='signature_reference')
    input_b = layers.Input(shape=input_shape, name='signature_test')
    
    # Shared feature extractor (same weights for both branches)
    feature_extractor = _build_feature_extractor(input_shape)
    
    # Extract features from both signatures
    features_a = feature_extractor(input_a)
    features_b = feature_extractor(input_b)
    
    # L1 Distance Custom Layer (Solves Keras Lambda deserialization bugs)
    L1DistanceLayer = _get_l1_layer()
    l1_distance = L1DistanceLayer(name='l1_distance')([features_a, features_b])
    
    # Additional dense layers for classification
    x = layers.Dense(512, activation='relu')(l1_distance)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    
    # Final prediction: 1 = genuine, 0 = forged
    prediction = layers.Dense(1, activation='sigmoid', name='output')(x)
    
    model = Model(inputs=[input_a, input_b], outputs=prediction, 
                  name='siamese_signature_verifier')
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.00006),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    return model


class SignatureVerifier:
    """
    High-level interface for signature verification.
    
    Usage:
        verifier = SignatureVerifier()
        result = verifier.verify("reference.png", "test.png")
        print(result)  # {'is_genuine': True, 'confidence': 0.94, ...}
    """
    
    def __init__(self):
        # Initialize common paths
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.MODEL_PATH = os.path.join(self.BASE_DIR, 'siamese_model.keras')
        self.TEMP_DIR = os.path.join(os.path.dirname(self.BASE_DIR), 'static', 'signatures')
        self.model = None
        self._verification_log = []  # Track predictions for analytics
    
    def _ensure_model_loaded(self):
        """Load or build the Siamese model."""
        if self.model is not None:
            return
        
        tf, _, _ = _lazy_import_tf()
        
        if os.path.exists(self.MODEL_PATH):
            print(f"[SignatureVerifier] Loading pre-trained model from {self.MODEL_PATH}")
            L1DistanceLayer = _get_l1_layer()
            self.model = tf.keras.models.load_model(
                self.MODEL_PATH,
                custom_objects={'L1DistanceLayer': L1DistanceLayer},
                compile=True,
                safe_mode=False
            )
        else:
            print("[SignatureVerifier] No pre-trained model found. Building new model...")
            self.model = build_siamese_model()
            self._initialize_with_synthetic_training()
    
    def _initialize_with_synthetic_training(self):
        """
        Initialize the model with a small synthetic training pass.
        This gives the model reasonable initial weights for demo purposes.
        
        In production, you would train on a real dataset like CEDAR or GPDS.
        """
        tf, _, _ = _lazy_import_tf()
        print("[SignatureVerifier] Running synthetic initialization training...")
        
        np.random.seed(42)
        
        # Generate synthetic training pairs
        n_pairs = 200
        img_shape = (105, 105, 1)
        
        # Genuine pairs: similar images with small perturbations
        ref_genuine = np.random.rand(n_pairs, *img_shape).astype(np.float32) * 0.5 + 0.25
        test_genuine = ref_genuine + np.random.normal(0, 0.05, ref_genuine.shape).astype(np.float32)
        test_genuine = np.clip(test_genuine, 0, 1)
        labels_genuine = np.ones(n_pairs)
        
        # Forged pairs: different random images
        ref_forged = np.random.rand(n_pairs, *img_shape).astype(np.float32) * 0.5 + 0.25
        test_forged = np.random.rand(n_pairs, *img_shape).astype(np.float32) * 0.5 + 0.25
        labels_forged = np.zeros(n_pairs)
        
        # Combine
        ref_all = np.concatenate([ref_genuine, ref_forged])
        test_all = np.concatenate([test_genuine, test_forged])
        labels_all = np.concatenate([labels_genuine, labels_forged])
        
        # Shuffle
        indices = np.random.permutation(len(labels_all))
        ref_all = ref_all[indices]
        test_all = test_all[indices]
        labels_all = labels_all[indices]
        
        # Train for a few epochs
        self.model.fit(
            [ref_all, test_all], labels_all,
            batch_size=32,
            epochs=10,
            validation_split=0.2,
            verbose=1
        )
        
        # Save the initialized model
        os.makedirs(self.BASE_DIR, exist_ok=True)
        self.model.save(self.MODEL_PATH)
        print(f"[SignatureVerifier] Model saved to {self.MODEL_PATH}")
    
    def verify(self, reference_image, test_image, threshold=0.5):
        """
        Verify if a test signature matches the reference signature.
        
        Args:
            reference_image: path, bytes, or PIL Image of the reference signature
            test_image: path, bytes, or PIL Image of the test signature
            threshold: confidence threshold (default 0.5)
                       above = genuine, below = forged
        
        Returns:
            dict with:
                - is_genuine (bool): whether the signature is genuine
                - confidence (float): similarity score between 0.0 and 1.0
                - verdict (str): "GENUINE" or "FORGED"
                - details (str): human-readable description
        """
        from .signature_utils import preprocess_signature
        
        self._ensure_model_loaded()
        
        # Preprocess both signatures
        ref_processed = preprocess_signature(reference_image)
        test_processed = preprocess_signature(test_image)
        
        # Get prediction from Siamese Network
        similarity_score = float(self.model.predict(
            [ref_processed, test_processed], verbose=0
        )[0][0])
        
        is_genuine = similarity_score >= threshold
        
        result = {
            'is_genuine': is_genuine,
            'confidence': round(similarity_score * 100, 2),
            'verdict': 'GENUINE' if is_genuine else 'FORGED',
            'threshold_used': threshold,
            'details': (
                f"Signature similarity score: {similarity_score:.4f}. "
                f"The test signature is {'a GENUINE match' if is_genuine else 'likely FORGED'}. "
                f"(Threshold: {threshold})"
            )
        }
        
        # Log for analytics
        self._verification_log.append({
            'confidence': similarity_score,
            'verdict': result['verdict']
        })
        
        return result
    
    def get_verification_history(self):
        """Return the verification log for analytics purposes."""
        return self._verification_log
    
    def get_model_summary(self):
        """Return model architecture summary as a string."""
        self._ensure_model_loaded()
        summary_lines = []
        self.model.summary(print_fn=lambda x: summary_lines.append(x))
        return '\n'.join(summary_lines)
