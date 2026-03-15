import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Home.css';

export default function Home() {
  const [hoverCard, setHoverCard] = useState(null);
  
  return (
    <div className="home">
      <section className="hero">
        <div className="hero-background">
          <div className="floating-waste plastic">🧴</div>
          <div className="floating-waste paper">📄</div>
          <div className="floating-waste metal">🔩</div>
          <div className="floating-waste organic">🍃</div>
        </div>
        <div className="hero-content">
          <h1 className="hero-title">SmartBin AI</h1>
          <p className="hero-subtitle">Smart Waste Segregation & Gamified Recycling System</p>
          <p className="hero-description">Take a photo of waste, earn points, and save the planet!</p>
          <Link to="/camera" className="cta-button">🚀 Start Classifying</Link>
        </div>
      </section>

      <section className="features">
        <h2>How It Works</h2>
        <div className="features-grid">
          {[
            { icon: '📸', title: 'Capture Waste', desc: 'Take a photo of any waste item using your camera', num: 1 },
            { icon: '🤖', title: 'AI Classification', desc: 'Our AI instantly identifies waste type (plastic, paper, metal, organic)', num: 2 },
            { icon: '📍', title: 'Disposal Guide', desc: 'Get exact location to dispose your waste properly', num: 3 },
            { icon: '⭐', title: 'Earn Points', desc: 'Collect points, badges, and climb the ranks', num: 4 },
            { icon: '🌍', title: 'Track Impact', desc: 'See your environmental impact and CO₂ saved', num: 5 },
            { icon: '🏆', title: 'Compete', desc: 'Join the leaderboard and compete with other eco-warriors', num: 6 },
          ].map((item, idx) => (
            <div
              key={idx}
              className="feature-card"
              onMouseEnter={() => setHoverCard(idx)}
              onMouseLeave={() => setHoverCard(null)}
              style={hoverCard === idx ? { transform: 'translateY(-8px)', boxShadow: '0 15px 35px rgba(0,0,0,0.15)' } : {}}
            >
              <div className="card-number">{item.num}</div>
              <span className="icon animate-bounce">{item.icon}</span>
              <h3>{item.title}</h3>
              <p>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="cta-section">
        <h2>Ready to Make a Difference?</h2>
        <Link to="/camera" className="cta-button-large">🌱 Start Your Journey Now</Link>
        <div className="stats-showcase">
          <div className="stat-item">
            <div className="stat-number">2527+</div>
            <div className="stat-label">Training Images</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">99%</div>
            <div className="stat-label">Accuracy</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">4</div>
            <div className="stat-label">Waste Types</div>
          </div>
        </div>
      </section>
    </div>
  );
}
