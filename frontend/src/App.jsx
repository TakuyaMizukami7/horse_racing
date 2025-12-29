import React from 'react';
import { Routes, Route } from 'react-router-dom';
import RaceInput from './components/RaceInput';

function App() {
  return (
    <>
      <header>
        <div className="container header-content">
          <div className="logo">
            <span>ANTIGRAVITY</span>
            <span style={{ fontWeight: 300, color: 'var(--text-secondary)' }}>RACING</span>
          </div>
          <a href="https://github.com/google-deepmind" target="_blank" className="btn btn-ghost" rel="noreferrer">
            GitHub
          </a>
        </div>
      </header>
      <main style={{ minHeight: 'calc(100vh - 70px)' }}>
        <Routes>
          <Route path="/" element={<RaceInput />} />
        </Routes>
      </main>
    </>
  );
}

export default App;
