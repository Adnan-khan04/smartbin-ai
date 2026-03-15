import React, { useState, useEffect } from 'react';
import './Leaderboard.css';

export default function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState([]);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const response = await fetch('/api/gamification/leaderboard');
      const data = await response.json();
      setLeaderboard(data.leaderboard || []);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div className="leaderboard">
      <h1>🏆 Global Leaderboard</h1>

      <div className="leaderboard-table">
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>User</th>
              <th>Points</th>
              <th>Items Recycled</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map((entry, index) => (
              <tr key={index} className={index < 3 ? 'top-3' : ''}>
                <td className="rank">{entry.rank}</td>
                <td className="user">{entry.user}</td>
                <td className="points">{entry.points}</td>
                <td>-</td>
              </tr>
            ))}
            {leaderboard.length === 0 && (
              <tr>
                <td colSpan="4" className="empty-message">No data available yet</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
