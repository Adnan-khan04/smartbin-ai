from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends, status
from pydantic import BaseModel, Field, validator
from typing import List
import io
from PIL import Image
import os
import tempfile
import importlib.util
from pathlib import Path
import time
import uuid
import jwt
import logging

logger = logging.getLogger(__name__)

# DB imports
from database import get_db, User as DBUser, Classification
from sqlalchemy.orm import Session

router = APIRouter()

class ClassificationResult(BaseModel):
    waste_type: str
    confidence: float
    probabilities: List[float] = []
    disposal_location: str
    description: str
    points_earned: int = 0
    awarded: bool = False
    requires_confirmation: bool = False
    used_heuristic: bool = False  # indicates ensemble/heuristic was used

class WasteCategory(BaseModel):
    plastic: str
    paper: str
    metal: str
    organic: str

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

# Disposal locations for each waste type
DISPOSAL_LOCATIONS = {
    "plastic": "Recycle Bin (Yellow Container)",
    "paper": "Paper Bin (Blue Container)",
    "metal": "Metal Bin (Gray Container)",
    "organic": "Organic Waste Bin (Green Container)",
}

WASTE_DESCRIPTIONS = {
    "plastic": "Plastic waste - can be recycled into new products",
    "paper": "Paper waste - can be recycled into pulp and new paper",
    "metal": "Metal waste - can be smelted and reused",
    "organic": "Organic waste - can be composted for soil enrichment",
}

# --- Connect to PyTorch model from ai-model/waste_classifier.py ---
# We import the module by path because the repo folder is `ai-model` (not a python package).
_backend_dir = Path(__file__).resolve().parents[1]
_ai_model_path = Path(__file__).resolve().parents[2] / "ai-model" / "waste_classifier.py"
_model_rel_path = os.getenv("MODEL_PATH", "./models/waste_classifier.pth")
_model_path = (_backend_dir / Path(_model_rel_path)).resolve()

_model = None
try:
    if _ai_model_path.exists():
        spec = importlib.util.spec_from_file_location("ai_waste", str(_ai_model_path))
        ai_waste = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ai_waste)

        # Ensure models directory exists
        _model_path.parent.mkdir(parents=True, exist_ok=True)

        # If saved model exists, load it; otherwise create & save a default (untrained) state dict so app can run
        if _model_path.exists():
            try:
                _model = ai_waste.load_model(str(_model_path))
            except Exception:
                _model = None
        else:
            try:
                # create a default model and save its state dict so future loads succeed
                default_model = ai_waste.WasteClassifier(num_classes=4)
                import torch
                torch.save(default_model.state_dict(), str(_model_path))
                _model = ai_waste.load_model(str(_model_path))
            except Exception:
                _model = None
    else:
        _model = None
except Exception:
    _model = None


AUTO_AWARD_THRESHOLD = float(os.getenv('AUTO_AWARD_THRESHOLD', 0.6))

@router.post("/image", response_model=ClassificationResult)
async def classify_waste(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Classify waste from image.
    - If user is authenticated and confidence >= AUTO_AWARD_THRESHOLD → award + persist automatically.
    - If confidence < AUTO_AWARD_THRESHOLD → return requires_confirmation=True and do not persist.
    Backend is authoritative for awarding points (fixes double-award).
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")
        
        if file.content_type and not file.content_type.startswith('image/'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image")

        contents = await file.read()
        
        if len(contents) > 10 * 1024 * 1024:  # 10MB max
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large (max 10MB)")

        # Run model (or heuristic fallback). Use an ensemble (model + lightweight color heuristic + simple TTA)
        used_heuristic = False
        if _model is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(contents)
                tmp_path = tmp.name

            debug_dir = _backend_dir / 'debug_captures'
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_file = debug_dir / f"capture_{int(time.time()*1000)}.jpg"
            try:
                with open(tmp_path, 'rb') as r, open(debug_file, 'wb') as w:
                    w.write(r.read())
            except Exception as e:
                logger.error(f"Failed to save debug capture: {str(e)}")
                debug_file = None

            try:
                # Use ONLY the trained model — no heuristic mixing, no TTA
                # The trained model is authoritative; heuristic only runs as last-resort fallback below
                pred_class, confidence, probs = ai_waste.predict_with_ensemble(_model, tmp_path, device='cpu', w_model=1.0, w_heur=0.0, tta=False)
                waste_type = pred_class
                used_heuristic = False
                logger.info(f"Model prediction: {waste_type} ({confidence:.4f}) | probs: {[f'{p:.4f}' for p in probs]}")
            except Exception as e:
                logger.error(f"Model prediction failed: {str(e)}")
                # fallback to heuristic-only prediction
                try:
                    pil = Image.open(tmp_path).convert('RGB')
                    heur = ai_waste._heuristic_scores_from_pil(pil)
                    import numpy as _np
                    idx = int(_np.argmax(_np.array(heur)))
                    classes = ['plastic', 'paper', 'metal', 'organic']
                    waste_type = classes[idx]
                    confidence = float(heur[idx])
                    probs = heur
                    used_heuristic = True
                except Exception:
                    waste_type = "plastic"
                    confidence = 0.95
                    probs = [float(confidence), 0.0, 0.0, 0.0]
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        else:
            logger.warning("Model not loaded, using heuristic fallback prediction")
            # heuristic-only prediction from image bytes
            try:
                pil = Image.open(io.BytesIO(contents)).convert('RGB')
                heur = ai_waste._heuristic_scores_from_pil(pil)
                import numpy as _np
                idx = int(_np.argmax(_np.array(heur)))
                classes = ['plastic', 'paper', 'metal', 'organic']
                waste_type = classes[idx]
                confidence = float(heur[idx])
                probs = heur
                used_heuristic = True
            except Exception:
                waste_type = "plastic"
                confidence = 0.95
                probs = [float(confidence), 0.0, 0.0, 0.0]

        # points that *would* be awarded for this classification
        pts = 10 + int(float(confidence) * 10)
        awarded = False
        requires_confirmation = float(confidence) < AUTO_AWARD_THRESHOLD

        # Auto-award only when user is authenticated AND confidence >= threshold
        try:
            auth = request.headers.get('authorization') or request.headers.get('Authorization')
            if auth and auth.lower().startswith('bearer '):
                token = auth.split(' ', 1)[1]
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username = payload.get('sub')
                if username and float(confidence) >= AUTO_AWARD_THRESHOLD:
                    user = db.query(DBUser).filter(DBUser.username == username).first()
                    if user:
                        user.points = (user.points or 0) + pts
                        record = Classification(
                            id=uuid.uuid4().hex,
                            user_id=user.id,
                            waste_type=waste_type,
                            confidence=float(confidence),
                            points_earned=pts,
                            image_path=str(debug_file) if 'debug_file' in locals() and debug_file else None
                        )
                        db.add(user)
                        db.add(record)
                        db.commit()
                        awarded = True
                        logger.info(f"Auto-awarded {pts} points to {username} for {waste_type} classification")
        except jwt.InvalidTokenError:
            logger.warning("Invalid token provided")
            db.rollback()
        except Exception as e:
            logger.error(f"Error processing classification: {str(e)}")
            db.rollback()

        return ClassificationResult(
            waste_type=waste_type,
            confidence=float(confidence),
            probabilities=probs,
            disposal_location=DISPOSAL_LOCATIONS.get(waste_type, "Unknown"),
            description=WASTE_DESCRIPTIONS.get(waste_type, "Unknown waste type"),
            points_earned=pts,
            awarded=awarded,
            requires_confirmation=requires_confirmation,
            used_heuristic=used_heuristic
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Classification endpoint error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Classification failed")


class ConfirmRequest(BaseModel):
    waste_type: str = Field(..., min_length=1, max_length=50)
    confidence: float = Field(..., ge=0.0, le=1.0)
    probabilities: List[float] = Field(default=[], max_items=10)

    @validator('waste_type')
    def validate_waste_type(cls, v):
        allowed = ['plastic', 'paper', 'metal', 'organic']
        if v.lower() not in allowed:
            raise ValueError(f'waste_type must be one of {allowed}')
        return v.lower()

    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('confidence must be between 0 and 1')
        return v


@router.post('/confirm')
async def confirm_classification(req: ConfirmRequest, request: Request, db: Session = Depends(get_db)):
    """Persist a classification and award points when a user confirms a low-confidence result."""
    try:
        # user must be authenticated to confirm
        auth = request.headers.get('authorization') or request.headers.get('Authorization')
        if not auth or not auth.lower().startswith('bearer '):
            logger.warning("Confirm classification: missing authentication")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required to confirm classification')

        token = auth.split(' ', 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get('sub')
            if not username:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
        except jwt.InvalidTokenError:
            logger.warning("Confirm classification: invalid token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')

        user = db.query(DBUser).filter(DBUser.username == username).first()
        if not user:
            logger.warning(f"Confirm classification: user not found - {username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

        # Idempotency: avoid duplicate confirmation within short window
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(seconds=60)
        existing = db.query(Classification).filter(
            Classification.user_id == user.id,
            Classification.waste_type == req.waste_type,
            Classification.created_at >= cutoff
        ).first()
        if existing:
            logger.info(f"Idempotent confirm: already processed for {username}")
            return {"awarded": True, "points_earned": existing.points_earned, "message": "Already confirmed"}

        pts = 10 + int(float(req.confidence) * 10)
        try:
            user.points = (user.points or 0) + pts
            record = Classification(
                id=uuid.uuid4().hex,
                user_id=user.id,
                waste_type=req.waste_type,
                confidence=float(req.confidence),
                points_earned=pts,
                image_path=None
            )
            db.add(user)
            db.add(record)
            db.commit()
            logger.info(f"Confirmed classification: {pts} points awarded to {username} for {req.waste_type}")
            return {"awarded": True, "points_earned": pts, "points": user.points}
        except Exception as e:
            db.rollback()
            logger.error(f"Confirm classification error for {username}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Confirm endpoint error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Confirmation failed")



@router.get("/categories", response_model=WasteCategory)
async def get_categories():
    """Get all waste categories"""
    return WasteCategory(
        plastic="Bottles, bags, containers, packaging",
        paper="Newspapers, magazines, cardboard, books",
        metal="Cans, foil, wires, utensils",
        organic="Food waste, leaves, grass, compost"
    )


@router.post('/upload-model')
async def upload_model(file: UploadFile = File(...)):
    """Upload a PyTorch .pth checkpoint and activate it (development use only)."""
    # basic validation
    if not file.filename.endswith('.pth'):
        raise HTTPException(status_code=400, detail='Only .pth checkpoint files are accepted')

    contents = await file.read()
    tmp_path = _model_path.parent / f"tmp_uploaded_{int(time.time()*1000)}.pth"
    with open(tmp_path, 'wb') as f:
        f.write(contents)

    # validate by trying to load
    try:
        test_model = ai_waste.load_model(str(tmp_path))
    except Exception as e:
        try:
            tmp_path.unlink()
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=f'Uploaded checkpoint is invalid: {e}')

    # backup existing model
    try:
        if _model_path.exists():
            bak = _model_path.parent / f"waste_classifier.pth.bak_{int(time.time())}"
            _model_path.replace(bak)
    except Exception:
        pass

    # move new checkpoint into place and reload global _model
    try:
        tmp_path.replace(_model_path)
        global _model
        _model = ai_waste.load_model(str(_model_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to activate uploaded model: {e}')

    # return a small sanity-check
    try:
        final_layer = _model.mobilenet.classifier[-1]
        bias = final_layer.bias.detach().cpu().numpy().tolist()
        import torch.nn.functional as F, torch
        logits = torch.tensor(bias).unsqueeze(0)
        probs = F.softmax(logits, dim=1).squeeze(0).tolist()
    except Exception:
        bias = None
        probs = None

    return {"success": True, "message": "Model uploaded and activated", "bias": bias, "bias_probs": probs}


@router.get('/model-info')
async def model_info():
    """Return basic info about the currently loaded model."""
    if _model is None:
        raise HTTPException(status_code=404, detail='No model loaded')
    try:
        final_layer = _model.mobilenet.classifier[-1]
        bias = final_layer.bias.detach().cpu().numpy().tolist()
    except Exception:
        bias = None

    return {"model_loaded": _model_path.exists(), "model_path": str(_model_path), "bias": bias}
