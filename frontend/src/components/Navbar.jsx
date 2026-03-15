import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

export default function Navbar() {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
    window.location.href = '/';
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="logo">
          <span>♻️</span> SmartBin AI
        </Link>
        <ul className="nav-menu">
          <li><Link to="/">Home</Link></li>
          <li><Link to="/camera">Classify Waste</Link></li>
          <li><Link to="/dashboard">Dashboard</Link></li>
          <li><Link to="/leaderboard">Leaderboard</Link></li>
          <li><Link to="/profile">Profile</Link></li>
          {!token ? (
            <li><Link to="/login">Login / Register</Link></li>
          ) : (
            <>
              <li className="nav-user">{user ? user.username : 'You'}</li>
              <li><button className="link-like" onClick={logout}>Logout</button></li>
            </>
          )}
        </ul>
      </div>
    </nav>
  );
} 
