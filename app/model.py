import torch
import torch.nn as nn
from aws_related.s3 import load_model
from torchvision import models

class AIImageDetector:
    def __init__(self, model_path: str = None):
        self.device = torch.device("cpu")
        self.model = models.resnet50(weights=True)
        self.model.fc = nn.Linear(self.model.fc.in_features, 2)
        if model_path:
            if model_path == "image":
                self.model.load_state_dict(load_model())
        self.model.eval()

    def predict(self, tensor):
        with torch.no_grad():
            batch = tensor.repeat(8, 1, 1, 1)
            outputs = self.model(batch)
            probs = torch.softmax(outputs, dim=1)
            confidences, predicted_classes = torch.max(probs, dim=1)
            predicted_class = predicted_classes[0]
            confidence = confidences[0]
            label = "AI-generated" if predicted_class.item() == 1 else "Real"
            return label, confidence.item()

detector = AIImageDetector(model_path="image")