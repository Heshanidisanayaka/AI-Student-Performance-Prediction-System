import React, { useState } from 'react';
import { X, UserCheck, AlertCircle } from 'lucide-react';

export default function AssignLecturerModal({ isOpen, onClose, onAssign, subject, isAssigning = false, error = null }) {
  const [lecturerId, setLecturerId] = useState(subject?.lecturer_id || '');

  if (!isOpen || !subject) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onAssign(subject.id, lecturerId ? Number(lecturerId) : null);
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog modal-small">
        <div className="modal-header">
          <h3>Assign Lead Lecturer</h3>
          <button type="button" className="icon-btn" onClick={onClose} disabled={isAssigning}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="modal-alert-error" style={{ margin: '1rem 1.5rem 0' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form">
          <p style={{ margin: '0 0 1rem 0', fontSize: '0.9rem', color: '#475569' }}>
            Assign a faculty lecturer to supervise <strong>{subject.code} - {subject.name}</strong>.
          </p>

          <div className="form-group">
            <label>Select Faculty Lecturer</label>
            <select
              value={lecturerId}
              onChange={(e) => setLecturerId(e.target.value)}
              className="filter-select"
            >
              <option value="">-- No Lecturer Assigned --</option>
              {/* Common university faculty test options */}
              <option value="2">Prof. Alan Turing (prof_turing@university.edu)</option>
              <option value="3">Prof. Donald Knuth (prof_knuth@university.edu)</option>
              <option value="1">System Administrator (system_admin@university.edu)</option>
            </select>
          </div>

          <div className="modal-actions" style={{ padding: '1rem 0 0', background: 'transparent' }}>
            <button type="button" className="btn-secondary" onClick={onClose} disabled={isAssigning}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={isAssigning}>
              <UserCheck size={16} />
              <span>{isAssigning ? 'Updating...' : 'Assign Lecturer'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
