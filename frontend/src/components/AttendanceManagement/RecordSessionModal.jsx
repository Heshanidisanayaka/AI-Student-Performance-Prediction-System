import React, { useState, useEffect } from 'react';
import { X, Check, UserX, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react';
import { subjectService } from '../../services/subjectService';
import { attendanceService } from '../../services/attendanceService';

export default function RecordSessionModal({ isOpen, onClose, subjects = [], onSuccess }) {
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [sessionName, setSessionName] = useState('Session 1');
  const [enrolledStudents, setEnrolledStudents] = useState([]);
  const [attendanceMap, setAttendanceMap] = useState({}); // { [studentId]: { status: 'present', remarks: '' } }
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // When subject changes, fetch enrolled students
  useEffect(() => {
    if (!selectedSubjectId) {
      setEnrolledStudents([]);
      setAttendanceMap({});
      return;
    }

    const fetchRoster = async () => {
      setLoadingStudents(true);
      setError(null);
      try {
        const data = await subjectService.getEnrolledStudents(selectedSubjectId);
        const list = Array.isArray(data) ? data : data.enrolled_students || [];
        setEnrolledStudents(list);

        // Initialize default 'present' for all enrolled students
        const initialMap = {};
        list.forEach((item) => {
          const sId = item.student ? item.student.id : item.id;
          initialMap[sId] = { status: 'present', remarks: '' };
        });
        setAttendanceMap(initialMap);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load enrolled students.');
      } finally {
        setLoadingStudents(false);
      }
    };

    fetchRoster();
  }, [selectedSubjectId]);

  if (!isOpen) return null;

  const handleStatusChange = (studentId, status) => {
    setAttendanceMap((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        status,
      },
    }));
  };

  const handleRemarksChange = (studentId, remarks) => {
    setAttendanceMap((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        remarks,
      },
    }));
  };

  const handleMarkAll = (status) => {
    const updated = { ...attendanceMap };
    enrolledStudents.forEach((item) => {
      const sId = item.student ? item.student.id : item.id;
      if (updated[sId]) {
        updated[sId] = { ...updated[sId], status };
      }
    });
    setAttendanceMap(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedSubjectId) {
      setError('Please select a subject.');
      return;
    }
    if (!sessionName.trim()) {
      setError('Session name cannot be empty.');
      return;
    }
    if (enrolledStudents.length === 0) {
      setError('No students available to mark attendance for this subject.');
      return;
    }

    const records = enrolledStudents.map((item) => {
      const sId = item.student ? item.student.id : item.id;
      const rec = attendanceMap[sId] || { status: 'present', remarks: '' };
      return {
        student_id: sId,
        status: rec.status,
        remarks: rec.remarks?.trim() || null,
      };
    });

    setSubmitting(true);
    setError(null);

    try {
      await attendanceService.recordSessionAttendance({
        subject_id: parseInt(selectedSubjectId, 10),
        date,
        session_name: sessionName.trim(),
        records,
      });
      onSuccess?.('Session attendance recorded successfully!');
      onClose();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to record session attendance.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content attendance-session-modal">
        <div className="modal-header">
          <div>
            <h3>Record Classroom Session Attendance</h3>
            <p className="modal-subtitle">
              Bulk-mark attendance for enrolled students. Duplicate entries for the same session are prevented.
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
          <div className="session-config-grid">
            <div className="form-group">
              <label>Select Subject *</label>
              <select
                value={selectedSubjectId}
                onChange={(e) => setSelectedSubjectId(e.target.value)}
                required
              >
                <option value="">-- Choose Subject --</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.code} - {s.name} ({s.academic_year})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Date *</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Session Identifier *</label>
              <input
                type="text"
                placeholder="e.g. Session 1, Lab 2, Tutorial"
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                maxLength={50}
                required
              />
            </div>
          </div>

          {/* Enrolled Students Roster */}
          <div className="session-roster-section">
            <div className="roster-toolbar">
              <div className="roster-heading">
                <h4>Enrolled Students Roster ({enrolledStudents.length})</h4>
                <span className="roster-note">
                  Excused absences are automatically excluded from performance penalties.
                </span>
              </div>
              {enrolledStudents.length > 0 && (
                <div className="bulk-quick-actions">
                  <button
                    type="button"
                    className="quick-btn quick-present"
                    onClick={() => handleMarkAll('present')}
                  >
                    <Check size={14} /> Mark All Present
                  </button>
                  <button
                    type="button"
                    className="quick-btn quick-absent"
                    onClick={() => handleMarkAll('absent')}
                  >
                    <UserX size={14} /> Mark All Absent
                  </button>
                </div>
              )}
            </div>

            {loadingStudents ? (
              <div className="roster-loading">
                <span className="spinner-sm"></span> Loading enrolled student roster...
              </div>
            ) : !selectedSubjectId ? (
              <div className="roster-empty-hint">
                Please select a subject above to load enrolled students.
              </div>
            ) : enrolledStudents.length === 0 ? (
              <div className="roster-empty-hint alert-warning">
                No students enrolled in this subject yet. Go to Subjects Management to enroll students.
              </div>
            ) : (
              <div className="roster-table-wrapper">
                <table className="roster-table">
                  <thead>
                    <tr>
                      <th>Student</th>
                      <th>Class & Year</th>
                      <th style={{ width: '250px' }}>Status</th>
                      <th>Remarks / Excuse Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {enrolledStudents.map((item) => {
                      const student = item.student || item;
                      const sId = student.id;
                      const currentStatus = attendanceMap[sId]?.status || 'present';
                      const currentRemarks = attendanceMap[sId]?.remarks || '';

                      return (
                        <tr key={sId}>
                          <td>
                            <div className="student-cell-info">
                              <span className="student-cell-name">
                                {student.first_name} {student.last_name}
                              </span>
                              <span className="student-cell-id">
                                {student.student_id_number}
                              </span>
                            </div>
                          </td>
                          <td>
                            <span className="tag-class">{student.class_name || 'Class A'}</span>
                          </td>
                          <td>
                            <div className="status-toggle-group">
                              <button
                                type="button"
                                className={`status-pill pill-present ${currentStatus === 'present' ? 'active' : ''}`}
                                onClick={() => handleStatusChange(sId, 'present')}
                              >
                                Present
                              </button>
                              <button
                                type="button"
                                className={`status-pill pill-absent ${currentStatus === 'absent' ? 'active' : ''}`}
                                onClick={() => handleStatusChange(sId, 'absent')}
                              >
                                Absent
                              </button>
                              <button
                                type="button"
                                className={`status-pill pill-excused ${currentStatus === 'excused' ? 'active' : ''}`}
                                onClick={() => handleStatusChange(sId, 'excused')}
                              >
                                Excused
                              </button>
                            </div>
                          </td>
                          <td>
                            <input
                              type="text"
                              className="remark-input"
                              placeholder={
                                currentStatus === 'excused'
                                  ? 'e.g. Medical certificate, varsity sports'
                                  : 'Optional note'
                              }
                              value={currentRemarks}
                              onChange={(e) => handleRemarksChange(sId, e.target.value)}
                            />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={submitting || enrolledStudents.length === 0}
            >
              {submitting ? 'Recording Session...' : 'Submit Attendance Session'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
