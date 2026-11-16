import React, { useState } from 'react';
import { GraduationCap, BookOpen, CalendarCheck, Sparkles } from 'lucide-react';
import StudentManagement from './pages/StudentManagement';
import SubjectManagement from './pages/SubjectManagement';
import AttendanceManagement from './pages/AttendanceManagement';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('students');

  return (
    <div className="app-container">
      {/* Top Application Navigation Bar */}
      <nav className="app-navbar">
        <div className="app-navbar-brand">
          <div className="brand-logo-glow">
            <Sparkles size={20} color="#fff" />
          </div>
          <div className="brand-titles">
            <span className="brand-name">PredicTech AI</span>
            <span className="brand-tagline">Real-Time Student Performance Prediction System</span>
          </div>
        </div>

        <div className="app-navbar-tabs">
          <button
            type="button"
            className={`nav-tab-btn ${activeTab === 'students' ? 'active' : ''}`}
            onClick={() => setActiveTab('students')}
          >
            <GraduationCap size={18} />
            <span>Students</span>
          </button>
          <button
            type="button"
            className={`nav-tab-btn ${activeTab === 'subjects' ? 'active' : ''}`}
            onClick={() => setActiveTab('subjects')}
          >
            <BookOpen size={18} />
            <span>Subjects & Modules</span>
          </button>
          <button
            type="button"
            className={`nav-tab-btn ${activeTab === 'attendance' ? 'active' : ''}`}
            onClick={() => setActiveTab('attendance')}
          >
            <CalendarCheck size={18} />
            <span>Attendance</span>
          </button>
        </div>
      </nav>

      {/* Main Content View */}
      <main className="app-main-content">
        {activeTab === 'students' && <StudentManagement />}
        {activeTab === 'subjects' && <SubjectManagement />}
        {activeTab === 'attendance' && <AttendanceManagement />}
      </main>
    </div>
  );
}

export default App;
