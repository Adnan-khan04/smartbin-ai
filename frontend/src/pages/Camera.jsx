import React, { useState, useRef, useEffect } from 'react';
import './Camera.css';

const CATEGORY_META = {
  plastic: { label: 'Plastic', color: '#F59E0B', emoji: '🧴', description: 'Recyclable plastic bottles, bags, containers' },
  paper: { label: 'Paper', color: '#3B82F6', emoji: '📄', description: 'Cardboard, newspapers, paper products' },
  metal: { label: 'Metal', color: '#6B7280', emoji: '🔩', description: 'Aluminum cans, steel, metal scraps' },
  organic: { label: 'Organic', color: '#10B981', emoji: '🍃', description: 'Food waste, leaves, compostable matter' },
};

export default function Camera() {
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);
  const [pointsBurst, setPointsBurst] = useState(null);
  const fileInputRef = useRef(null);

  // Camera states
  const [currentStep, setCurrentStep] = useState(1); // 1: Choose input, 2: Capture, 3: Review
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [cameraOn, setCameraOn] = useState(false);
  const [facingMode, setFacingMode] = useState('environment'); // 'user' or 'environment'

  useEffect(() => {
    return () => stopCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startCamera = async (mode = facingMode) => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Camera not supported in this browser. Use file upload instead.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: mode }, audio: false });
      streamRef.current = stream;
      setCameraOn(true);
      setCurrentStep(2);
      await new Promise((r) => requestAnimationFrame(r));
      if (videoRef.current) {
        try {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        } catch (playErr) {
          console.warn('Video play failed:', playErr);
        }
      }
    } catch (err) {
      console.error('Camera error', err);
      alert('Could not access camera. Check permissions or try file upload.');
      setCameraOn(false);
      streamRef.current = null;
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
    setCurrentStep(1);
  };

  const switchCamera = async () => {
    const next = facingMode === 'environment' ? 'user' : 'environment';
    setFacingMode(next);
    stopCamera();
    setTimeout(() => startCamera(next), 250);
  };

  const captureFromVideo = () => {
    const v = videoRef.current;
    if (!v || !v.readyState || v.readyState < 2) {
      alert('Camera not ready. Please wait a moment and try again.');
      return;
    }
    const canvas = document.createElement('canvas');
    canvas.width = v.videoWidth || v.width || 640;
    canvas.height = v.videoHeight || v.height || 480;

    if (canvas.width < 100 || canvas.height < 100) {
      alert('Camera resolution too low. Please try again.');
      return;
    }

    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(v, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      if (!blob || blob.size === 0) {
        alert('Failed to capture image. Please try again.');
        return;
      }
      const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
      setImage(URL.createObjectURL(file));
      setCurrentStep(3);
      await handleImageCapture(file);
    }, 'image/jpeg', 0.95);
  };

  const handleImageCapture = async (file) => {
    setResult(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/classify/image', {
        method: 'POST',
        body: formData,
        headers: localStorage.getItem('token') ? { Authorization: `Bearer ${localStorage.getItem('token')}` } : {}
      });
      const data = await response.json();
      setResult(data);

      if (data && data.awarded) {
        const pts = data.points_earned || 0;
        setPointsBurst(pts);
        setShowConfetti(true);
        setTimeout(() => setShowConfetti(false), 2200);
        setTimeout(() => setPointsBurst(null), 2000);

        try {
          const u = JSON.parse(localStorage.getItem('user') || '{}');
          if (u && u.user_id) {
            u.points = (u.points || 0) + pts;
            localStorage.setItem('user', JSON.stringify(u));
          }
        } catch (err) { /* ignore */ }
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error classifying image');
    } finally {
      setLoading(false);
    }
  };

  const clearResult = () => {
    setResult(null);
    setImage(null);
    setPointsBurst(null);
    setCurrentStep(1);
    stopCamera();
  };

  const categories = ['plastic', 'paper', 'metal', 'organic'];

  const getConfidenceLevel = (c) => (c >= 0.85 ? 'high' : c >= 0.6 ? 'medium' : 'low');

  return (
    <div className="camera-container">
      {/* Hero Section */}
      <div className="camera-hero">
        <div className="hero-content">
          <h1>🎯 Classify Your Waste</h1>
          <p>Help us build a greener future by classifying waste properly</p>
        </div>
        <div className="hero-decoration">
          <div className="floating-item plastic">🧴</div>
          <div className="floating-item paper">📄</div>
          <div className="floating-item metal">🔩</div>
          <div className="floating-item organic">🍃</div>
        </div>
      </div>

      {/* Step Indicator */}
      <div className="step-indicator">
        <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
          <div className="step-number">1</div>
          <div className="step-label">Choose Method</div>
        </div>
        <div className="step-connector"></div>
        <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
          <div className="step-number">2</div>
          <div className="step-label">Capture</div>
        </div>
        <div className="step-connector"></div>
        <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
          <div className="step-number">3</div>
          <div className="step-label">Results</div>
        </div>
      </div>

      <div className="camera-main">
        {/* Left Section - Image/Video Preview */}
        <div className="preview-section">
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => e.target.files && handleImageCapture(e.target.files[0])}
            accept="image/*"
            style={{ display: 'none' }}
          />

          {!cameraOn && !image && !result && (
            <div className="empty-state">
              <div className="empty-icon">📸</div>
              <p>No image selected</p>
              <small>Upload or capture to get started</small>
            </div>
          )}

          {cameraOn && !image && (
            <div className="video-container">
              <video ref={videoRef} className="video-preview" playsInline muted autoPlay />
              <div className="video-overlay">📹 LIVE</div>
            </div>
          )}

          {image && (
            <div className="image-container">
              <img src={image} alt="Captured waste" className="image-preview" />
            </div>
          )}

          {result && !loading && (
            <div className="result-preview">
              <img src={image} alt="Captured waste" className="result-image" />
              <div className="result-overlay">
                <div className="result-overlay-content">
                  <div className="result-emoji" style={{ background: CATEGORY_META[result.waste_type]?.color }}>
                    {CATEGORY_META[result.waste_type]?.emoji}
                  </div>
                  <div className="result-overlay-text">
                    <div className="result-type">{CATEGORY_META[result.waste_type]?.label}</div>
                    <div className="result-confidence">{(result.confidence * 100).toFixed(0)}% Confidence</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {loading && (
            <div className="loading-state">
              <div className="spinner-large"></div>
              <p>Analyzing your waste...</p>
            </div>
          )}
        </div>

        {/* Right Section - Controls or Results */}
        <div className="control-section">
          {!cameraOn && !image && !result && (
            <div className="input-options">
              <div className="option-label">How would you like to capture?</div>
              <button onClick={() => fileInputRef.current?.click()} className="option-button primary">
                <span className="option-icon">📁</span>
                <span className="option-text">
                  <span className="option-title">Upload Photo</span>
                  <span className="option-desc">Choose from your gallery</span>
                </span>
              </button>
              <button onClick={() => startCamera()} className="option-button secondary">
                <span className="option-icon">📷</span>
                <span className="option-text">
                  <span className="option-title">Take Photo</span>
                  <span className="option-desc">Use your device camera</span>
                </span>
              </button>
            </div>
          )}

          {cameraOn && !image && (
            <div className="camera-controls">
              <button className="capture-btn" onClick={captureFromVideo}>
                <div className="capture-ring"></div>
              </button>
              <div className="camera-actions">
                <button className="icon-btn" onClick={switchCamera} title="Switch camera">
                  🔄
                </button>
                <button className="icon-btn close" onClick={stopCamera} title="Close camera">
                  ✕
                </button>
              </div>
            </div>
          )}

          {result && (
            <div className="result-details">
              <div className="result-card-header">
                <div className="waste-badge" style={{ background: CATEGORY_META[result.waste_type]?.color }}>
                  {CATEGORY_META[result.waste_type]?.emoji}
                </div>
                <div className="waste-info">
                  <h2>{CATEGORY_META[result.waste_type]?.label}</h2>
                  <p>{CATEGORY_META[result.waste_type]?.description}</p>
                </div>
              </div>

              <div className="result-stats">
                <div className="stat">
                  <span className="stat-label">Confidence</span>
                  <span className={`stat-value conf-${getConfidenceLevel(result.confidence)}`}>
                    {(result.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="stat">
                  <span className="stat-label">Method</span>
                  <span className="stat-value">{result.used_heuristic ? 'Ensemble' : 'Model'}</span>
                </div>
              </div>

              <div className="disposal-guide">
                <div className="guide-label">📍 Disposal Guide</div>
                <div className="guide-text">{result.disposal_location}</div>
              </div>

              <div className="probabilities">
                <div className="prob-label">Detection Breakdown</div>
                {categories.map((c, i) => {
                  const p = (result.probabilities && result.probabilities[i]) || 0;
                  const meta = CATEGORY_META[c];
                  return (
                    <div className="prob-item" key={c}>
                      <div className="prob-info">
                        <span className="prob-emoji" style={{ background: meta.color }}>{meta.emoji}</span>
                        <span className="prob-name">{meta.label}</span>
                      </div>
                      <div className="prob-bar">
                        <div className="prob-fill" style={{ width: `${Math.round(p * 100)}%`, background: meta.color }} />
                      </div>
                      <span className="prob-percent">{Math.round(p * 100)}%</span>
                    </div>
                  );
                })}
              </div>

              <div className="result-actions">
                <button onClick={clearResult} className="action-btn primary">
                  ✓ Correct
                </button>
                <button onClick={() => { setImage(null); setResult(null); }} className="action-btn secondary">
                  ↻ Retry
                </button>
              </div>

              <div className="points-earned-animated" aria-hidden>
                {pointsBurst && <div className="points-burst">+{pointsBurst} pts 🎉</div>}
                {showConfetti && (
                  <div className="confetti">
                    {Array.from({ length: 18 }).map((_, idx) => <span key={idx} className="confetti-piece" />)}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
