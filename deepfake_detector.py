import tensorflow as tf
import numpy as np
import cv2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepFakeDetector:
    def __init__(self, model_path):
        try:
            self.model = tf.keras.models.load_model(model_path)
            logger.info("Model loaded successfully")
            # Print model summary to verify architecture
            self.model.summary()
        except Exception as e:
            raise Exception(f"Failed to load model: {str(e)}")

    def preprocess_frame(self, frame):
        """Preprocess the frame for model input"""
        try:
            # Resize to expected input size (assuming 224x224 - adjust based on your model)
            frame = cv2.resize(frame, (224, 224))
            
            # Convert to RGB if in BGR
            if frame.shape[-1] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Normalize pixel values to [0, 1] range
            frame = frame.astype(np.float32) / 255.0
            
            # Add batch dimension
            frame = np.expand_dims(frame, axis=0)
            
            logger.info(f"Frame preprocessed successfully. Shape: {frame.shape}")
            return frame
            
        except Exception as e:
            logger.error(f"Error in preprocessing: {str(e)}")
            raise

    def predict_frame(self, frame):
        """
        Predict whether a frame is real or fake
        Returns: (prediction_label, confidence_score)
        """
        try:
            # Validate frame
            self.validate_frame(frame)
            
            # Preprocess the frame
            processed_frame = self.preprocess_frame(frame)
            
            # Get model prediction
            prediction = self.model.predict(processed_frame, verbose=0)
            
            # Log raw prediction for debugging
            logger.info(f"Raw prediction: {prediction}")
            
            # Get confidence score (ensure it's between 0 and 1)
            confidence = float(prediction[0][0]) if len(prediction.shape) == 2 else float(prediction[0])
            confidence = np.clip(confidence, 0, 1)
            
            logger.info(f"Clipped confidence score: {confidence}")
            
            # Determine if the frame is real or fake
            # Model output: closer to 0 = real, closer to 1 = fake
            is_fake = confidence >= 0.5
            
            # Calculate confidence percentage (0-100%)
            confidence_percent = confidence * 100 if is_fake else (1 - confidence) * 100
            confidence_percent = round(confidence_percent, 2)  # Round to 2 decimal places
            
            # Return prediction label and confidence
            result = ("Fake" if is_fake else "Real", confidence_percent)
            logger.info(f"Final prediction: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise Exception(f"Prediction failed: {str(e)}")

    def validate_frame(self, frame):
        """Validate frame before prediction"""
        try:
            if frame is None:
                raise ValueError("Frame is None")
            
            if not isinstance(frame, np.ndarray):
                raise ValueError("Frame must be a numpy array")
            
            if len(frame.shape) != 3:
                raise ValueError("Frame must be a 3D array (height, width, channels)")
            
            if frame.shape[-1] != 3:
                raise ValueError("Frame must have 3 channels (RGB/BGR)")
                
            logger.info("Frame validation passed")
                
        except Exception as e:
            logger.error(f"Frame validation failed: {str(e)}")
            raise