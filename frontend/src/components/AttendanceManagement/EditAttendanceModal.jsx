import React, { useState, useEffect } from 'react';
import { X, AlertCircle } from 'lucide-react';
import { attendanceService } from '../../services/attendanceService';

export default function EditAttendanceModal({ isOpen, onClose, record, onSuccess }) {
  const [status, setStatus] = useState('present');
  const [remarks, setRemarks] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (record) {
      setStatus(record.status || 'present');
      setRemarks(record.remarks || '');
      setError(null);
    }
  }, [record]);

  if (!isOpen || !record) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await attendanceService.updateAttendance(record.id, {
        status,
        remarks: remarks.trim() || null,
      });
      onSuccess?.('Attendance record updated successfully.');
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update attendance record.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content modal-sm">
        <div className="modal-header">
          <div>
            <h3>Update Attendance Record</h3>
            <p className="modal-subtitle">
              Modify status or document an official excused absence reason.
            </p>
          </div>
          <button type="button" className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="modal-error-banner">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="record-details-summary">
            <div className="summary-row">
              <span className="summary-label">Student:</span>
              <span className="summary-value">
                {record.student_name} ({record.student_id_number})
              </span>
            </div>
            <div className="summary-row">
              <span className="summary-label">Subject:</span>
              <span className="summary-value">
                {record.subject_code} - {record.subject_name}
              </span>
            </div>
            <div className="summary-row">
              <span className="summary-label">Session & Date:</span>
              <span className="summary-value">
                {record.session_name} on {record.date}
              </span>
            </div>
          </div>

          <div className="form-group" style={{ marginTop: '1rem' }}>
            <label>Attendance Status *</label>
            <div className="status-toggle-group full-width">
              <button
                type="button"
                className={`status-pill pill-present ${status === 'present' ? 'active' : ''}`}
                onClick={() => setStatus('present')}
              >
                Present
              </button>
              <button
                type="button"
                className={`status-pill pill-absent ${status === 'absent' ? 'active' : ''}`}
                onClick={() => setStatus('absent')}
              >
                Absent
              </button>
              <button
                type="button"
                className={`status-pill pill-excused ${status === 'excused' ? 'active' : ''}`}
                onClick={() => setStatus('excused')}
              >
                Excused
              </button>
            </div>
          </div>

          <div className="form-group">
            <label>Remarks / Excused Reason</label>
            <input
              type="text"
              placeholder="e.g. Medical certificate verified, Dean approval"
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              maxLength={255}
            />
            <span className="form-hint">
              Institutional policy excludes excused absences from penalty denominators.
            </span>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
