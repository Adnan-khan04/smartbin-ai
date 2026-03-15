"""
Download TrashNet dataset from HuggingFace and train the waste classifier.
This script:
1. Downloads the TrashNet dataset (2527 images from Stanford)
2. Maps 6 classes (glass/paper/cardboard/plastic/metal/trash) to our 4 classes
3. Trains the MobileNetV2 model
4. Saves trained weights
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import os
from pathlib import Path
import json
from tqdm import tqdm
import shutil
from datasets import load_dataset
import numpy as np

# Configuration
NUM_EPOCHS = 15
BATCH_SIZE = 32
LEARNING_RATE = 0.001
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MODEL_SAVE_PATH = '../models/waste_classifier.pth'

# Our 4-class mapping
TARGET_CLASSES = ['plastic', 'paper', 'metal', 'organic']

# TrashNet classes to our classes mapping
CLASS_MAPPING = {
    'glass': 'plastic',      # Glass -> Plastic (recyclable)
    'paper': 'paper',
    'cardboard': 'paper',    # Cardboard -> Paper
    'plastic': 'plastic',
    'metal': 'metal',
    'trash': 'organic'       # Trash -> Organic (compostable/waste)
}

class WasteDataset(torch.utils.data.Dataset):
    """Custom dataset loading from local directory structure"""
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.classes = TARGET_CLASSES
        self.images = []
        self.labels = []
        
        for idx, class_name in enumerate(self.classes):
            class_dir = os.path.join(root_dir, class_name)
            if os.path.exists(class_dir):
                for img_file in os.listdir(class_dir):
                    if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                        self.images.append(os.path.join(class_dir, img_file))
                        self.labels.append(idx)
        
        print(f"[WasteDataset] Loaded {len(self.images)} images from {root_dir}")
        for i, cls in enumerate(self.classes):
            count = sum(1 for l in self.labels if l == i)
            print(f"  {cls}: {count} images")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            print(f"Error loading {img_path}: {e}")
            # Return a dummy image
            image = Image.new('RGB', (224, 224), color='white')
        
        label = self.labels[idx]
        
        if self.transform:
            image = self.transform(image)
        
        return image, label

class WasteClassifier(nn.Module):
    """MobileNetV2-based waste classifier"""
    def __init__(self, num_classes=4):
        super(WasteClassifier, self).__init__()
        self.mobilenet = models.mobilenet_v2(pretrained=True)
        
        # Freeze earlier layers for transfer learning
        for param in self.mobilenet.features[:-4].parameters():
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

def download_and_prepare_data(data_dir='./trashnet_data'):
    """Download TrashNet dataset and organize into class folders"""
    print("[1] Downloading TrashNet dataset from HuggingFace...")
    
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Load dataset from HuggingFace
        dataset = load_dataset('garythung/trashnet', split='train', trust_remote_code=True)
        print(f"[✓] Downloaded {len(dataset)} images from TrashNet")
        
        # Create class directories
        for cls in TARGET_CLASSES:
            os.makedirs(os.path.join(data_dir, cls), exist_ok=True)
        
        # Organize images into class folders
        print("[2] Organizing images into class folders...")
        for idx, example in enumerate(tqdm(dataset, desc="Processing images")):
            if idx % 100 == 0:
                print(f"  Processed {idx}/{len(dataset)} images")
            
            try:
                # Get image and label
                image = example['image']
                label = example['label']
                
                # Map TrashNet class to our classes
                dataset_classes = ['glass', 'paper', 'cardboard', 'plastic', 'metal', 'trash']
                if label < len(dataset_classes):
                    old_class = dataset_classes[label]
                    new_class = CLASS_MAPPING.get(old_class, 'organic')
                else:
                    new_class = 'organic'
                
                # Save image to appropriate folder
                class_dir = os.path.join(data_dir, new_class)
                os.makedirs(class_dir, exist_ok=True)
                
                img_path = os.path.join(class_dir, f'trashnet_{idx:05d}.jpg')
                if isinstance(image, Image.Image):
                    image.save(img_path)
                else:
                    image = Image.fromarray(np.array(image))
                    image.save(img_path)
            
            except Exception as e:
                print(f"  Error processing image {idx}: {e}")
                continue
        
        print(f"[✓] Data preparation complete. Total: {sum(len(os.listdir(os.path.join(data_dir, cls))) for cls in TARGET_CLASSES)} images")
        return data_dir
    
    except Exception as e:
        print(f"[!] Failed to download from HuggingFace: {e}")
        print("[*] Trying alternative download method...")
        
        # Fallback: use a simpler approach with PIL and requests
        import urllib.request
        import tarfile
        
        dataset_url = "https://huggingface.co/datasets/garythung/trashnet/resolve/main/data/dataset-resized.zip"
        zip_path = os.path.join(data_dir, 'dataset.zip')
        
        print(f"[*] Downloading from {dataset_url}...")
        urllib.request.urlretrieve(dataset_url, zip_path)
        
        print("[*] Extracting dataset...")
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(data_dir)
        
        os.remove(zip_path)
        print(f"[✓] Dataset downloaded and extracted")
        return data_dir

def train_model(data_dir):
    """Train the waste classifier model"""
    print("\n[3] Setting up training...")
    print(f"Device: {DEVICE}")
    
    # Data transforms
    train_transform = transforms.Compose([
        transforms.RandomRotation(15),
        transforms.RandomHorizontalFlip(),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    # Load dataset
    full_dataset = WasteDataset(data_dir, transform=train_transform)
    
    # Split into train/val
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    # Re-apply validation transform
    val_dataset.dataset.transform = val_transform
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)
    
    print(f"Train samples: {len(train_dataset)}, Val samples: {len(val_dataset)}")
    
    # Model, loss, optimizer
    model = WasteClassifier(num_classes=len(TARGET_CLASSES)).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)
    
    best_val_acc = 0.0
    
    print(f"\n[4] Training for {NUM_EPOCHS} epochs...")
    print("=" * 80)
    
    for epoch in range(NUM_EPOCHS):
        # Training phase
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        with tqdm(train_loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS} [Train]") as pbar:
            for images, labels in pbar:
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                
                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                train_correct += (predicted == labels).sum().item()
                train_total += labels.size(0)
                
                pbar.set_postfix({'loss': train_loss / (train_total / BATCH_SIZE)})
        
        train_acc = 100 * train_correct / train_total
        train_loss /= len(train_loader)
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            with tqdm(val_loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS} [Val]") as pbar:
                for images, labels in pbar:
                    images, labels = images.to(DEVICE), labels.to(DEVICE)
                    outputs = model(images)
                    loss = criterion(outputs, labels)
                    
                    val_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    val_correct += (predicted == labels).sum().item()
                    val_total += labels.size(0)
                    
                    pbar.set_postfix({'loss': val_loss / (val_total / BATCH_SIZE)})
        
        val_acc = 100 * val_correct / val_total
        val_loss /= len(val_loader)
        
        scheduler.step()
        
        print(f"Epoch {epoch+1:2d} | Train Loss: {train_loss:.4f}, Acc: {train_acc:.2f}% | Val Loss: {val_loss:.4f}, Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
            torch.save(model.state_dict(), MODEL_SAVE_PATH)
            print(f"  [✓] Model saved (best val acc: {best_val_acc:.2f}%)")
    
    print("=" * 80)
    print(f"[✓] Training complete! Best validation accuracy: {best_val_acc:.2f}%")
    return MODEL_SAVE_PATH

def evaluate_model(model_path, data_dir):
    """Evaluate model on test data"""
    print(f"\n[5] Evaluating model...")
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    dataset = WasteDataset(data_dir, transform=val_transform)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    model = WasteClassifier(num_classes=len(TARGET_CLASSES)).to(DEVICE)
    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    model.eval()
    
    correct = 0
    total = 0
    class_correct = [0] * len(TARGET_CLASSES)
    class_total = [0] * len(TARGET_CLASSES)
    
    with torch.no_grad():
        for images, labels in tqdm(dataloader, desc="Evaluating"):
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            for i in range(len(TARGET_CLASSES)):
                class_total[i] += (labels == i).sum().item()
                class_correct[i] += ((predicted == i) * (labels == i)).sum().item()
    
    print(f"\nOverall Accuracy: {100 * correct / total:.2f}%")
    print("\nPer-class Accuracy:")
    for i, cls in enumerate(TARGET_CLASSES):
        if class_total[i] > 0:
            acc = 100 * class_correct[i] / class_total[i]
            print(f"  {cls:10s}: {acc:6.2f}% ({class_correct[i]}/{class_total[i]})")

if __name__ == '__main__':
    print("\n" + "="*80)
    print("TrashNet Dataset Download & Model Training")
    print("="*80)
    
    # Step 1: Download and prepare data
    data_dir = download_and_prepare_data('./trashnet_data')
    
    # Step 2: Train model
    model_path = train_model(data_dir)
    
    # Step 3: Evaluate
    evaluate_model(model_path, data_dir)
    
    print("\n[✓] All done!")
    print(f"[✓] Trained model saved to: {os.path.abspath(model_path)}")
