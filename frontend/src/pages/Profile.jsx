import React, { useState, useEffect } from 'react';
import './Profile.css';

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('token') || sessionStorage.getItem('token');
      if (!token) return;
      const response = await fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) return;
      const data = await response.json();
      setProfile(data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div className="profile">
      <h1>My Profile</h1>

      {profile && (
        <div className="profile-card">
          <div className="profile-header">
            <div className="avatar">{profile.username?.[0]?.toUpperCase()}</div>
            <div className="profile-info">
              <h2>{profile.username}</h2>
              <p>{profile.email}</p>
              <div className="profile-stats">
                <div className="stat-inline">
                  <strong>{profile.points ?? 0}</strong>
                  <small>points</small>
                </div>
                <div className="stat-inline">
                  <strong>Lv {profile.level ?? 1}</strong>
                  <small>level</small>
                </div>
                <div className="stat-inline">
                  <strong>{profile.rank ?? 'Novice'}</strong>
                  <small>rank</small>
                </div>
              </div>
              <p className="joined">Joined {profile.joined_date}</p>
            </div>
          </div>

          <div className="profile-bio">
            <h3>About</h3>
            <p>{profile.bio || 'No bio yet'}</p>
          </div>

          <div className="profile-actions">
            <button className="edit-btn">Edit Profile</button>
            <button className="logout-btn">Logout</button>
          </div>
        </div>
      )}
    </div>
  );
}
