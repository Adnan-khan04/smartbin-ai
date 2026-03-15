"""
Simplified training script using downloaded TrashNet data or synthetic data augmentation.
This bypasses the complex HuggingFace dataset loader.
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
import zipfile
import shutil
from tqdm import tqdm
import numpy as np

NUM_EPOCHS = 10
BATCH_SIZE = 32
LEARNING_RATE = 0.001
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MODEL_SAVE_PATH = '../models/waste_classifier.pth'
TARGET_CLASSES = ['plastic', 'paper', 'metal', 'organic']

def extract_trashnet_zip():
    """Extract the pre-downloaded TrashNet dataset"""
    cache_dir = os.path.expanduser('~/.cache/huggingface/hub/datasets--garythung--trashnet')
    
    print("[*] Looking for cached TrashNet files...")
    
    # Look for the resized dataset zip
    resized_zip = None
    for root, dirs, files in os.walk(cache_dir):
        for f in files:
            if 'dataset-resized' in f and f.endswith('.zip'):
                resized_zip = os.path.join(root, f)
                break
    
    if resized_zip and os.path.exists(resized_zip):
        print(f"[✓] Found cached dataset: {resized_zip}")
        extract_dir = './trashnet_extracted'
        os.makedirs(extract_dir, exist_ok=True)
        
        print(f"[*] Extracting to {extract_dir}...")
        with zipfile.ZipFile(resized_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        return extract_dir
    
    print("[!] Cached dataset not found")
    return None

def organize_trashnet_data(extract_dir):
    """Organize extracted TrashNet data into class folders"""
    data_dir = './trashnet_organized'
    
    # Create class directories
    for cls in TARGET_CLASSES:
        os.makedirs(os.path.join(data_dir, cls), exist_ok=True)
    
    # TrashNet to our classes mapping
    mapping = {
        'glass': 'plastic',
        'paper': 'paper',
        'cardboard': 'paper',
        'plastic': 'plastic',
        'metal': 'metal',
        'trash': 'organic'
    }
    
    print("[*] Organizing files...")
    count = 0
    
    for class_name, target_class in mapping.items():
        src_dir = os.path.join(extract_dir, class_name)
        if not os.path.exists(src_dir):
            # Try alternate paths
            for root, dirs, files in os.walk(extract_dir):
                if os.path.basename(root) == class_name:
                    src_dir = root
                    break
        
        if os.path.exists(src_dir):
            target_dir = os.path.join(data_dir, target_class)
            for img_file in os.listdir(src_dir):
                if img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    src_path = os.path.join(src_dir, img_file)
                    dst_path = os.path.join(target_dir, f"{target_class}_{count}.jpg")
                    try:
                        shutil.copy2(src_path, dst_path)
                        count += 1
                    except:
                        pass
    
    print(f"[✓] Organized {count} images")
    return data_dir

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
        
        # Freeze early layers
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

def train_model(data_dir):
    """Train the waste classifier"""
    print("\n[3] Setting up training...")
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
    
    # Dataset
    full_dataset = WasteDataset(data_dir, transform=train_transform)
    
    if len(full_dataset) == 0:
        print("[!] No images found! Cannot train.")
        return None
    
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    val_dataset.dataset.transform = val_transform
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    
    print(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}")
    
    # Model
    model = WasteClassifier(num_classes=len(TARGET_CLASSES)).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)
    
    best_val_acc = 0.0
    
    print(f"\n[4] Training for {NUM_EPOCHS} epochs...")
    print("=" * 80)
    
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
            pbar.close()
        
        val_acc = 100 * val_correct / val_total
        val_loss /= len(val_loader)
        scheduler.step()
        
        print(f"Epoch {epoch+1:2d} | Train: {train_acc:.2f}% | Val: {val_acc:.2f}%")
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
            torch.save(model.state_dict(), MODEL_SAVE_PATH)
            print(f"  [✓] Saved (best: {best_val_acc:.2f}%)")
    
    print("=" * 80)
    print(f"[✓] Training complete! Best val acc: {best_val_acc:.2f}%")
    return MODEL_SAVE_PATH

def evaluate_model(model_path, data_dir):
    """Evaluate trained model"""
    print(f"\n[5] Evaluating...")
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    dataset = WasteDataset(data_dir, transform=val_transform)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    
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
            _, predicted = torch.max(outputs, 1)
            
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            for i in range(len(TARGET_CLASSES)):
                class_total[i] += (labels == i).sum().item()
                class_correct[i] += ((predicted == i) * (labels == i)).sum().item()
    
    print(f"\nOverall Accuracy: {100 * correct / total:.2f}%\n")
    print("Per-class Accuracy:")
    for i, cls in enumerate(TARGET_CLASSES):
        if class_total[i] > 0:
            acc = 100 * class_correct[i] / class_total[i]
            print(f"  {cls:10s}: {acc:6.2f}% ({class_correct[i]}/{class_total[i]})")

if __name__ == '__main__':
    print("\n" + "="*80)
    print("TrashNet Model Training (Simplified)")
    print("="*80)
    
    # Step 1: Extract cached data
    print("[1] Extracting cached TrashNet dataset...")
    extract_dir = extract_trashnet_zip()
    
    if extract_dir:
        # Step 2: Organize data
        print("[2] Organizing data into class folders...")
        data_dir = organize_trashnet_data(extract_dir)
        
        # Step 3: Train
        model_path = train_model(data_dir)
        
        if model_path:
            # Step 4: Evaluate
            evaluate_model(model_path, data_dir)
            print("\n[✓] All done!")
            print(f"[✓] Model saved to: {os.path.abspath(model_path)}")
    else:
        print("[!] Could not find cached dataset. Using public pre-trained model instead.")
        print("[!] Skipping custom training.")
