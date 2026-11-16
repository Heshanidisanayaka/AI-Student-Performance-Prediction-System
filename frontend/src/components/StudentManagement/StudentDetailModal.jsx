import React from 'react';
import { X, GraduationCap, Calendar, Mail, Building, BookOpen, Activity } from 'lucide-react';

export default function StudentDetailModal({ isOpen, onClose, student }) {
  if (!isOpen || !student) return null;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <span className="status-badge status-active">Active</span>;
      case 'at_risk':
        return <span className="status-badge status-at-risk">At Risk</span>;
      case 'graduated':
        return <span className="status-badge status-graduated">Graduated</span>;
      default:
        return <span className="status-badge status-suspended">{status}</span>;
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog">
        <div className="modal-header">
          <div className="detail-header-info">
            <h3>Student Profile</h3>
            <span className="id-sub">{student.student_id_number}</span>
          </div>
          <button type="button" className="icon-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="detail-modal-body">
          <div className="profile-banner">
            <div className="avatar-large">
              {student.first_name[0]}
              {student.last_name[0]}
            </div>
            <div>
              <h4>
                {student.first_name} {student.last_name}
              </h4>
              <p className="detail-email">{student.email}</p>
              <div className="badge-row">{getStatusBadge(student.status)}</div>
            </div>
          </div>

          <div className="info-grid">
            <div className="info-card">
              <Building size={18} className="info-icon" />
              <div>
                <label>Department</label>
                <span>{student.department}</span>
              </div>
            </div>

            <div className="info-card">
              <BookOpen size={18} className="info-icon" />
              <div>
                <label>Class & Section</label>
                <span>{student.class_name}</span>
              </div>
            </div>

            <div className="info-card">
              <Calendar size={18} className="info-icon" />
              <div>
                <label>Academic Year</label>
                <span>{student.academic_year}</span>
              </div>
            </div>

            <div className="info-card">
              <GraduationCap size={18} className="info-icon" />
              <div>
                <label>Current Semester</label>
                <span>Semester {student.current_semester}</span>
              </div>
            </div>
          </div>

          <div className="stats-cards-row">
            <div className="stat-card">
              <Activity size={18} color="#3b82f6" />
              <div>
                <h5>{student.attendance_count ?? 0}</h5>
                <label>Attendance Sessions</label>
              </div>
            </div>
            <div className="stat-card">
              <BookOpen size={18} color="#10b981" />
              <div>
                <h5>{student.records_count ?? 0}</h5>
                <label>Academic Records</label>
              </div>
            </div>
            <div className="stat-card">
              <GraduationCap size={18} color="#8b5cf6" />
              <div>
                <h5>{student.predictions_count ?? 0}</h5>
                <label>AI Predictions</label>
              </div>
            </div>
          </div>
        </div>

        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
