"""
Improved training script with class weighting to handle imbalanced dataset.
The TrashNet dataset has imbalanced classes (organic=137, metal=410, paper=997, plastic=983).
This script uses weighted loss to improve minority class detection.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split, Dataset
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import os
from pathlib import Path
from tqdm import tqdm
import numpy as np

NUM_EPOCHS = 15
BATCH_SIZE = 32
LEARNING_RATE = 0.001
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MODEL_SAVE_PATH = '../models/waste_classifier_balanced.pth'
TARGET_CLASSES = ['plastic', 'paper', 'metal', 'organic']

class WasteDataset(Dataset):
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
                    if img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        self.images.append(os.path.join(class_dir, img_file))
                        self.labels.append(idx)
        
        print(f"[WasteDataset] Loaded {len(self.images)} images")
        for i, cls in enumerate(self.classes):
            count = sum(1 for l in self.labels if l == i)
            print(f"  {cls}: {count} images")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        try:
            image = Image.open(img_path).convert('RGB')
        except:
            image = Image.new('RGB', (224, 224), color='white')
        
        label = self.labels[idx]
        
        if self.transform:
            image = self.transform(image)
        
        return image, label

class WasteClassifier(nn.Module):
    def __init__(self, num_classes=4):
        super(WasteClassifier, self).__init__()
        self.mobilenet = models.mobilenet_v2(pretrained=True)
        
        # Freeze early layers for transfer learning
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

def compute_class_weights(labels, num_classes):
    """Compute weights inversely proportional to class frequency"""
    class_counts = np.bincount(labels, minlength=num_classes)
    print(f"\nClass counts: {dict(zip(TARGET_CLASSES, class_counts))}")
    
    # Weight inversely proportional to frequency
    weights = 1.0 / (class_counts + 1)
    weights = weights / weights.sum() * num_classes
    
    print(f"Class weights: {dict(zip(TARGET_CLASSES, weights))}")
    return torch.FloatTensor(weights)

def train_model(data_dir):
    """Train with class-weighted loss"""
    print("\n[Setup] Training with class-weighted loss")
    print(f"Device: {DEVICE}")
    
    train_transform = transforms.Compose([
        transforms.RandomRotation(15),
        transforms.RandomHorizontalFlip(),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Load dataset
    full_dataset = WasteDataset(data_dir, transform=train_transform)
    
    if len(full_dataset) == 0:
        print("[!] No images found!")
        return None
    
    # Split
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    val_dataset.dataset.transform = val_transform
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    
    print(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}\n")
    
    # Compute class weights from training data
    train_labels = [full_dataset.labels[i] for i in train_dataset.indices]
    class_weights = compute_class_weights(train_labels, len(TARGET_CLASSES))
    class_weights = class_weights.to(DEVICE)
    
    # Model
    model = WasteClassifier(num_classes=len(TARGET_CLASSES)).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=class_weights)  # Weighted loss!
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=4, gamma=0.5)
    
    best_val_acc = 0.0
    
    print(f"[Training] {NUM_EPOCHS} epochs with weighted loss\n" + "="*80)
    
    for epoch in range(NUM_EPOCHS):
        # Train
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS} [Train]")
        for images, labels in pbar:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            train_correct += (predicted == labels).sum().item()
            train_total += labels.size(0)
        
        train_acc = 100 * train_correct / train_total
        train_loss /= len(train_loader)
        pbar.close()
        
        # Validate
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        class_correct = [0] * len(TARGET_CLASSES)
        class_total = [0] * len(TARGET_CLASSES)
        
        with torch.no_grad():
            pbar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS} [Val]")
            for images, labels in pbar:
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                val_correct += (predicted == labels).sum().item()
                val_total += labels.size(0)
                
                for i in range(len(TARGET_CLASSES)):
                    class_total[i] += (labels == i).sum().item()
                    class_correct[i] += ((predicted == i) * (labels == i)).sum().item()
            pbar.close()
        
        val_acc = 100 * val_correct / val_total
        val_loss /= len(val_loader)
        scheduler.step()
        
        print(f"Epoch {epoch+1:2d} | Train: {train_acc:6.2f}% | Val: {val_acc:6.2f}%", end="")
        
        # Show per-class accuracy
        print(" | Per-class: ", end="")
        for i, cls in enumerate(TARGET_CLASSES):
            if class_total[i] > 0:
                acc = 100 * class_correct[i] / class_total[i]
                print(f"{cls[:4]}={acc:5.1f}% ", end="")
        print()
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
            torch.save(model.state_dict(), MODEL_SAVE_PATH)
            print(f"  [✓] Saved (best: {best_val_acc:.2f}%)")
    
    print("="*80)
    print(f"[Complete] Best validation accuracy: {best_val_acc:.2f}%")
    return MODEL_SAVE_PATH

if __name__ == '__main__':
    print("\n" + "="*80)
    print("RETRAINING WITH CLASS-WEIGHTED LOSS")
    print("="*80)
    
    data_dir = './trashnet_organized'
    
    if os.path.exists(data_dir):
        model_path = train_model(data_dir)
        if model_path:
            print(f"\n[Success] Model saved to: {os.path.abspath(model_path)}")
    else:
        print(f"[Error] Data directory not found: {data_dir}")
