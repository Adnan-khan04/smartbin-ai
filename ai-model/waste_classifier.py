import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision import models
from torch.utils.data import DataLoader, Dataset
import os
from pathlib import Path
from PIL import Image
import numpy as np
import argparse
import json

class WasteDataset(Dataset):
    """Custom dataset for waste classification"""
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.classes = ['plastic', 'paper', 'metal', 'organic']
        self.images = []
        self.labels = []
        
        # Load image paths and labels
        for idx, class_name in enumerate(self.classes):
            class_dir = os.path.join(root_dir, class_name)
            if os.path.exists(class_dir):
                for img_file in os.listdir(class_dir):
                    if img_file.endswith(('.jpg', '.jpeg', '.png')):
                        self.images.append(os.path.join(class_dir, img_file))
                        self.labels.append(idx)
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        image = Image.open(img_path).convert('RGB')
        label = self.labels[idx]
        
        if self.transform:
            image = self.transform(image)
        
        return image, label

class WasteClassifier(nn.Module):
    """Waste classification model using MobileNetV2"""
    def __init__(self, num_classes=4):
        super(WasteClassifier, self).__init__()
        
        # Load pre-trained MobileNetV2
        self.mobilenet = models.mobilenet_v2(pretrained=True)
        
        # Freeze early layers
        for param in self.mobilenet.features[:-2].parameters():
            param.requires_grad = False
        
        # Replace classifier
        input_features = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(input_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        return self.mobilenet(x)

def train_model(data_dir, epochs=10, batch_size=32, learning_rate=0.001, model_save_path='../models/waste_classifier.pth'):
    """Train the waste classification model and save checkpoint to `model_save_path`."""
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Data transforms
    train_transform = transforms.Compose([
        transforms.RandomRotation(10),
        transforms.RandomHorizontalFlip(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    # Create dataset and dataloader
    dataset = WasteDataset(data_dir, transform=train_transform)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Model, loss, optimizer
    model = WasteClassifier(num_classes=4).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training loop
    for epoch in range(epochs):
        total_loss = 0
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)
            
            # Forward pass
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        print(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.4f}")
    
    # Save model
    model_save_path = Path(model_save_path)
    model_save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), str(model_save_path))
    print(f"Model saved to {model_save_path}")
    
    return model

def load_model(model_path):
    """Load trained model — handles both checkpoint formats:
    - Old format: keys prefixed with 'mobilenet.' (WasteClassifier wrapper)
    - New format: flat MobileNetV2 keys ('features.*', 'classifier.*')
    """
    sd = torch.load(model_path, map_location='cpu', weights_only=False)

    # Detect format by checking first key
    first_key = next(iter(sd))
    if first_key.startswith('mobilenet.'):
        # Old format — load directly into WasteClassifier
        model = WasteClassifier(num_classes=4)
        model.load_state_dict(sd)
    else:
        # New format — flat MobileNetV2 state dict
        # Build a plain MobileNetV2 with our custom classifier head
        backbone = models.mobilenet_v2(weights=None)
        in_features = backbone.classifier[1].in_features
        backbone.classifier = torch.nn.Sequential(
            torch.nn.Dropout(0.5),
            torch.nn.Linear(in_features, 512),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.3),
            torch.nn.Linear(512, 4),
        )
        backbone.load_state_dict(sd)
        # Wrap in WasteClassifier shell so the rest of the code works unchanged
        model = WasteClassifier(num_classes=4)
        model.mobilenet = backbone
    return model

def predict(model, image_path, device='cpu'):
    """Predict waste type from image (returns top class + confidence)."""
    model.to(device)
    model.eval()
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    image = Image.open(image_path).convert('RGB')
    image = transform(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(image)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)
    
    classes = ['plastic', 'paper', 'metal', 'organic']
    return classes[predicted.item()], confidence.item()


def _heuristic_scores_from_pil(pil_img):
    """Compute a simple heuristic score vector [plastic, paper, metal, organic]
    based on color statistics. This is lightweight and intended as a fallback
    / ensemble signal when model confidence is low or dataset is limited.
    """
    import numpy as _np
    img = pil_img.convert('RGB')
    arr = _np.array(img)
    
    # Convert to HSV for color analysis
    hsv = Image.fromarray(arr).convert('HSV')
    h, s, v = _np.array(hsv).T

    total = float(arr.shape[0] * arr.shape[1])
    
    # Green detection (organic waste)
    green_mask = ((h >= 35) & (h <= 90)) & (s > 40) & (v > 30)
    green_ratio = green_mask.sum() / max(1.0, total)
    
    # Brown detection (organic waste, soil, compost)
    brown_mask = ((h >= 10) & (h <= 35)) & (s > 20) & (v < 200) & (v > 50)
    brown_ratio = brown_mask.sum() / max(1.0, total)
    
    # Grey/metallic detection (metal, dark surfaces)
    grey_mask = (s < 20) & (v > 80) & (v < 210)
    grey_ratio = grey_mask.sum() / max(1.0, total)
    
    # Bright white/very light detection (paper, cardboard)
    # More restrictive: very high value AND very low saturation
    bright_white_mask = (v > 220) & (s < 30) & (s < (v - 190))  # extremely low saturation
    bright_white_ratio = bright_white_mask.sum() / max(1.0, total)
    
    # Colorful detection (plastic tends to be vibrant)
    sat_mean = float(s.mean()) / 255.0
    val_mean = float(v.mean()) / 255.0
    colorfulness = sat_mean * (1.0 - (val_mean - 0.5) ** 2)  # penalize very light or dark
    
    # Red/pink detection (plastic often has red tones)
    red_mask = ((h >= 0) & (h <= 15)) | (h >= 240) & (s > 40) & (v > 50)
    red_ratio = red_mask.sum() / max(1.0, total)
    
    # Blue/purple detection (plastic often has blue tones)
    blue_mask = ((h >= 120) & (h <= 180)) & (s > 30) & (v > 50)
    blue_ratio = blue_mask.sum() / max(1.0, total)
    
    # Build heuristic scores (more balanced weights)
    organic_score = (green_ratio * 1.5) + (brown_ratio * 1.3)
    paper_score = bright_white_ratio * 1.2  # Lower weight for paper
    metal_score = grey_ratio * 1.1
    plastic_score = (colorfulness * 1.2) + (red_ratio * 0.8) + (blue_ratio * 0.8)
    
    scores = _np.array([plastic_score, paper_score, metal_score, organic_score], dtype=float)
    
    # if all zeros, provide a small uniform prior
    if scores.sum() <= 0:
        scores = _np.ones_like(scores) * 0.25
    
    probs = (scores / scores.sum()).tolist()
    return probs


def predict_with_ensemble(model, image_path, device='cpu', w_model=0.85, w_heur=0.15, tta=True):
    """Predict using model + lightweight heuristic ensemble with optional TTA.

    - Runs model prediction (with optional simple TTA: rotations) to get model_probs.
    - Computes heuristic_probs from image color stats.
    - Returns weighted combination: final_probs = normalize(w_model*model_probs + w_heur*heuristic_probs)

    Returns same tuple as predict_with_probs: (predicted_class, confidence, probabilities)
    """
    model.to(device)
    model.eval()

    pil = Image.open(image_path).convert('RGB')

    # model transform
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    # collect model probabilities (with simple TTA)
    tta_angles = [0, 90, 270] if tta else [0]
    model_probs_accum = None
    with torch.no_grad():
        for ang in tta_angles:
            img = pil.rotate(ang, expand=True) if ang != 0 else pil
            tensor = transform(img).unsqueeze(0).to(device)
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1).squeeze(0).cpu().numpy()
            if model_probs_accum is None:
                model_probs_accum = probs
            else:
                model_probs_accum += probs
        model_probs = (model_probs_accum / float(len(tta_angles))).tolist()

    # heuristic probabilities
    heur_probs = _heuristic_scores_from_pil(pil)

    # weighted combination
    import numpy as _np
    m = _np.array(model_probs, dtype=float)
    h = _np.array(heur_probs, dtype=float)
    final = (w_model * m) + (w_heur * h)
    if final.sum() <= 0:
        final = _np.ones_like(final) * (1.0 / len(final))
    final_probs = (final / final.sum()).tolist()

    # pick argmax
    confidence_idx = int(max(range(len(final_probs)), key=lambda i: final_probs[i]))
    confidence = float(final_probs[confidence_idx])

    classes = ['plastic', 'paper', 'metal', 'organic']
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Model probs: {[f'{p:.4f}' for p in model_probs]}")
    logger.debug(f"Heuristic probs: {[f'{p:.4f}' for p in heur_probs]}")
    logger.debug(f"Final probs (w_model={w_model}, w_heur={w_heur}): {[f'{p:.4f}' for p in final_probs]}")
    logger.debug(f"Predicted: {classes[confidence_idx]} (confidence: {confidence:.4f})")
    
    return classes[confidence_idx], confidence, final_probs


# keep the original predict_with_probs for backward compatibility (unchanged)
def predict_with_probs(model, image_path, device='cpu'):
    """Predict waste type and return the full probability vector.

    Returns: (predicted_class:str, confidence:float, probabilities:List[float])
    """
    model.to(device)
    model.eval()

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    image = Image.open(image_path).convert('RGB')
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)

    classes = ['plastic', 'paper', 'metal', 'organic']
    return classes[predicted.item()], confidence.item(), probabilities.squeeze(0).cpu().numpy().tolist()

def evaluate_dataset(model_or_path, data_dir, batch_size=32, device='cpu'):
    """Evaluate a trained model (or checkpoint path) on a labeled dataset directory.

    Dataset must have subdirectories named: plastic, paper, metal, organic
    Returns: dict with overall_accuracy, per_class_accuracy, confusion_matrix, num_samples
    """
    if isinstance(model_or_path, (str, Path)):
        model = load_model(str(model_or_path))
    else:
        model = model_or_path
    model.to(device)
    model.eval()

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    dataset = WasteDataset(data_dir, transform=eval_transform)
    if len(dataset) == 0:
        raise ValueError('No images found in dataset')
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    all_preds = []
    all_labels = []
    with torch.no_grad():
        for imgs, labels in loader:
            imgs = imgs.to(device)
            outputs = model(imgs)
            preds = torch.argmax(torch.softmax(outputs, dim=1), dim=1).cpu().numpy().tolist()
            all_preds.extend(preds)
            all_labels.extend(labels.numpy().tolist())

    num_classes = 4
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(all_labels, all_preds):
        cm[t, p] += 1

    per_class_acc = []
    for i in range(num_classes):
        total = cm[i].sum()
        per_class_acc.append(float(cm[i, i]) / total if total > 0 else None)

    overall_acc = float(np.trace(cm)) / float(max(1, cm.sum()))
    return {
        'overall_accuracy': overall_acc,
        'per_class_accuracy': per_class_acc,
        'confusion_matrix': cm.tolist(),
        'num_samples': len(all_labels)
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Waste classifier training/evaluation utility')
    sub = parser.add_subparsers(dest='cmd')

    t = sub.add_parser('train')
    t.add_argument('--data-dir', required=True)
    t.add_argument('--epochs', type=int, default=10)
    t.add_argument('--batch-size', type=int, default=32)
    t.add_argument('--lr', type=float, default=0.001)
    t.add_argument('--model-save-path', default='../backend/models/waste_classifier.pth')

    e = sub.add_parser('evaluate')
    e.add_argument('--model-path', required=True)
    e.add_argument('--data-dir', required=True)
    e.add_argument('--batch-size', type=int, default=32)

    p = sub.add_parser('predict')
    p.add_argument('--model-path', required=True)
    p.add_argument('--image', required=True)

    args = parser.parse_args()
    if args.cmd == 'train':
        train_model(args.data_dir, epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr, model_save_path=args.model_save_path)
    elif args.cmd == 'evaluate':
        import json
        res = evaluate_dataset(args.model_path, args.data_dir, batch_size=args.batch_size)
        print(json.dumps(res, indent=2))
    elif args.cmd == 'predict':
        model = load_model(args.model_path)
        pred, conf, probs = predict_with_probs(model, args.image, device='cpu')
        print(json.dumps({'prediction': pred, 'confidence': conf, 'probabilities': probs}, indent=2))
    else:
        parser.print_help()
