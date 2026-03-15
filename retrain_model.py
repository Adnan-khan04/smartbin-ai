"""
Resume training waste classifier from saved checkpoint (epoch 4, 85.3%).
Continues with same augmentation, class-weighting, and cosine LR schedule.
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split, Dataset, WeightedRandomSampler
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import os
import shutil
import numpy as np
from pathlib import Path
from tqdm import tqdm

# ── Config ─────────────────────────────────────────────────────────────────────
BASE       = Path(__file__).resolve().parent
DATA_DIR   = BASE / 'ai-model' / 'trashnet_organized'
SAVE_PATH  = BASE / 'models' / 'waste_classifier.pth'
BACKEND_MODEL = BASE / 'backend' / 'models' / 'waste_classifier.pth'
CLASSES    = ['plastic', 'paper', 'metal', 'organic']
TOTAL_EPOCHS = 20
RESUME_EPOCH = 4        # We already completed epochs 1-4
BATCH_SIZE = 32
LR         = 5e-4
DEVICE     = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

print(f"Device: {DEVICE}")
print(f"Data:   {DATA_DIR}")
print(f"Save:   {SAVE_PATH}")
print(f"Resuming from epoch {RESUME_EPOCH}, training to epoch {TOTAL_EPOCHS}")

# ── Dataset ────────────────────────────────────────────────────────────────────
class WasteDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.transform = transform
        self.images = []
        self.labels = []
        for idx, cls in enumerate(CLASSES):
            d = Path(root_dir) / cls
            if d.exists():
                for f in d.glob('*.jpg'):
                    self.images.append(str(f))
                    self.labels.append(idx)
        print(f"Dataset: {len(self.images)} images")
        for i, c in enumerate(CLASSES):
            n = sum(1 for l in self.labels if l == i)
            print(f"  {c}: {n}")

    def __len__(self): return len(self.images)

    def __getitem__(self, idx):
        try:
            img = Image.open(self.images[idx]).convert('RGB')
        except Exception:
            img = Image.new('RGB', (224, 224), (128, 128, 128))
        if self.transform:
            img = self.transform(img)
        return img, self.labels[idx]

# ── Transforms ─────────────────────────────────────────────────────────────────
train_tf = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.6, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(p=0.2),
    transforms.RandomRotation(30),
    transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.3, hue=0.1),
    transforms.RandomGrayscale(p=0.05),
    transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.1),
])

val_tf = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

# ── Load data ──────────────────────────────────────────────────────────────────
full_ds = WasteDataset(DATA_DIR, transform=train_tf)
if len(full_ds) == 0:
    print("ERROR: No images found!")
    exit(1)

train_n = int(0.85 * len(full_ds))
val_n   = len(full_ds) - train_n
train_ds, val_ds = random_split(full_ds, [train_n, val_n],
                                generator=torch.Generator().manual_seed(42))

class SubsetWithTransform(Dataset):
    def __init__(self, subset, transform):
        self.subset = subset
        self.transform = transform
    def __len__(self): return len(self.subset)
    def __getitem__(self, idx):
        img_path = self.subset.dataset.images[self.subset.indices[idx]]
        label    = self.subset.dataset.labels[self.subset.indices[idx]]
        try:
            img = Image.open(img_path).convert('RGB')
        except Exception:
            img = Image.new('RGB', (224, 224), (128, 128, 128))
        return self.transform(img), label

val_ds_proper = SubsetWithTransform(val_ds, val_tf)

# Weighted sampler to balance classes during training
train_labels = [full_ds.labels[i] for i in train_ds.indices]
class_counts = np.bincount(train_labels, minlength=len(CLASSES))
class_weights_arr = 1.0 / (class_counts.astype(float) + 1e-6)
sample_weights = [class_weights_arr[l] for l in train_labels]
sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
val_loader   = DataLoader(val_ds_proper, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

print(f"\nTrain: {len(train_ds)}, Val: {len(val_ds_proper)}")

# ── Build model architecture ──────────────────────────────────────────────────
backbone = models.mobilenet_v2(weights=None)  # No pretrained -- we load our checkpoint
in_features = backbone.classifier[1].in_features
backbone.classifier = nn.Sequential(
    nn.Dropout(0.5),
    nn.Linear(in_features, 512),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(512, len(CLASSES)),
)

# ── Load saved checkpoint ─────────────────────────────────────────────────────
print(f"\nLoading checkpoint from: {SAVE_PATH}")
sd = torch.load(str(SAVE_PATH), map_location='cpu', weights_only=False)
backbone.load_state_dict(sd)
print("  [OK] Checkpoint loaded successfully")

model = backbone.to(DEVICE)

# Loss with class weights (inverse frequency)
class_weights_tensor = torch.FloatTensor(class_weights_arr / class_weights_arr.sum() * len(CLASSES)).to(DEVICE)
criterion = nn.CrossEntropyLoss(weight=class_weights_tensor, label_smoothing=0.1)

# Two-phase LR: backbone gets lower LR, classifier gets higher
optimizer = optim.AdamW([
    {'params': model.features.parameters(), 'lr': LR * 0.1},
    {'params': model.classifier.parameters(), 'lr': LR},
], weight_decay=1e-4)

scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=TOTAL_EPOCHS, eta_min=1e-6)

# Fast-forward the scheduler to the resume epoch
for _ in range(RESUME_EPOCH):
    scheduler.step()
print(f"  [OK] LR scheduler advanced to epoch {RESUME_EPOCH}")

# ── Training (resume from epoch RESUME_EPOCH+1) ───────────────────────────────
best_val_acc = 85.3  # Previous best from epoch 4
print(f"\nResuming training from epoch {RESUME_EPOCH+1}...\n" + "="*70)

for epoch in range(RESUME_EPOCH, TOTAL_EPOCHS):
    # Train
    model.train()
    train_loss, train_correct, train_total = 0.0, 0, 0
    for imgs, labels in tqdm(train_loader, desc=f"Ep {epoch+1:02d}/{TOTAL_EPOCHS} [Train]", leave=False):
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        out  = model(imgs)
        loss = criterion(out, labels)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        train_loss    += loss.item()
        train_correct += (out.argmax(1) == labels).sum().item()
        train_total   += labels.size(0)

    # Validate
    model.eval()
    val_correct, val_total = 0, 0
    class_correct = [0] * len(CLASSES)
    class_total   = [0] * len(CLASSES)
    with torch.no_grad():
        for imgs, labels in val_loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            out  = model(imgs)
            pred = out.argmax(1)
            val_correct += (pred == labels).sum().item()
            val_total   += labels.size(0)
            for i in range(len(CLASSES)):
                class_correct[i] += ((pred == i) & (labels == i)).sum().item()
                class_total[i]   += (labels == i).sum().item()

    train_acc = 100 * train_correct / max(1, train_total)
    val_acc   = 100 * val_correct   / max(1, val_total)
    scheduler.step()

    per_class = " | ".join(
        f"{CLASSES[i][:4]}={100*class_correct[i]/max(1,class_total[i]):.0f}%"
        for i in range(len(CLASSES))
    )
    print(f"Ep {epoch+1:02d} | Train {train_acc:.1f}% | Val {val_acc:.1f}% | {per_class}")

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), str(SAVE_PATH))
        print(f"         [SAVED] (best={best_val_acc:.1f}%)")

print(f"\n{'='*70}")
print(f"Training complete. Best val accuracy: {best_val_acc:.1f}%")
print(f"Model saved to: {SAVE_PATH}")

# ── Copy to backend ───────────────────────────────────────────────────────────
BACKEND_MODEL.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(str(SAVE_PATH), str(BACKEND_MODEL))
print(f"  [OK] Copied model to: {BACKEND_MODEL}")

# ── Sanity check ──────────────────────────────────────────────────────────────
print("\n=== Sanity check (3 samples per class) ===")
model.eval()
correct, total = 0, 0
for cls in CLASSES:
    d = DATA_DIR / cls
    imgs = list(d.glob('*.jpg'))[-3:]
    for p in imgs:
        img = Image.open(p).convert('RGB')
        t   = val_tf(img).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            probs = torch.softmax(model(t), dim=1).squeeze(0).cpu().tolist()
        pred = CLASSES[int(np.argmax(probs))]
        ok   = "[OK]" if pred == cls else "[X]"
        if pred == cls: correct += 1
        total += 1
        print(f"  {ok} True={cls:8s} Pred={pred:8s}  [{', '.join(f'{p:.2f}' for p in probs)}]")
print(f"\nSanity: {correct}/{total} = {100*correct/total:.0f}%")
