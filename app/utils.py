from PIL import Image
import io
from torchvision import transforms

def preprocess_image(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize((448, 448)),
        transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                            [0.229, 0.224, 0.225])
    ])
    return transform(image).unsqueeze(0) 
