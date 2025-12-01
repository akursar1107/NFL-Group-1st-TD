import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Standings from './pages/Standings';
import BestBets from './pages/BestBets';
import Analysis from './pages/Analysis';
import WeeklyGames from './pages/WeeklyGames';
import NewPick from './pages/NewPick';
import EditPick from './pages/EditPick';
import AllPicks from './pages/AllPicks';
import UserDetail from './pages/UserDetail';
import AdminDashboard from './pages/AdminDashboard';
import EditUsers from './pages/EditUsers';
import GradePicks from './pages/GradePicks';
import Login from './pages/Login';
import UserProfile from './pages/UserProfile';
import './App.css';

function App() {
  return (
    <div>
      <Router>
        <nav style={{ 
          padding: '1rem', 
          background: '#fff', 
          color: '#000', 
          display: 'flex', 
          gap: '1rem', 
          borderBottom: '1px solid #ccc',
          position: 'sticky',
          top: 0,
          zIndex: 1000
        }}>
          <Link style={{ color: '#000', textDecoration: 'none', fontWeight: 'bold' }} to="/">Standings</Link>
          <Link style={{ color: '#000', textDecoration: 'none', fontWeight: 'bold' }} to="/best-bets">Best Bets</Link>
          <Link style={{ color: '#000', textDecoration: 'none', fontWeight: 'bold' }} to="/analysis">Analysis</Link>
          <Link style={{ color: '#000', textDecoration: 'none', fontWeight: 'bold' }} to="/weekly-games">Weekly Games</Link>
          <Link style={{ color: '#000', textDecoration: 'none', fontWeight: 'bold' }} to="/new-pick">New Pick</Link>
          <Link style={{ color: '#000', textDecoration: 'none', fontWeight: 'bold' }} to="/all-picks">All Picks</Link>
          <Link style={{ color: '#000', textDecoration: 'none', fontWeight: 'bold' }} to="/admin">Admin</Link>
          <Link style={{ color: '#000', textDecoration: 'none', fontWeight: 'bold' }} to="/login">Login</Link>
          <Link style={{ color: '#000', textDecoration: 'none', fontWeight: 'bold' }} to="/profile">Profile</Link>
        </nav>
        <div style={{ padding: '2rem' }}>
          <Routes>
            <Route path="/" element={<Standings />} />
            <Route path="/best-bets" element={<BestBets />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/weekly-games" element={<WeeklyGames />} />
            <Route path="/new-pick" element={<NewPick />} />
            <Route path="/edit-pick/:pickId" element={<EditPick />} />
            <Route path="/all-picks" element={<AllPicks />} />
            <Route path="/user/:userId" element={<UserDetail />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/edit-users" element={<EditUsers />} />
            <Route path="/grade-picks" element={<GradePicks />} />
            <Route path="/login" element={<Login />} />
            <Route path="/profile" element={<UserProfile />} />
          </Routes>
        </div>
      </Router>
    </div>
  );
}

export default App;
