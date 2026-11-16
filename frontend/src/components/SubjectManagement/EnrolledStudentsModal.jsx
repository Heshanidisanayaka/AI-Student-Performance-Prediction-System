import React, { useState, useEffect, useCallback } from 'react';
import { X, UserPlus, Trash2, Users, AlertCircle, CheckCircle2 } from 'lucide-react';
import { subjectService } from '../../services/subjectService';
import { studentService } from '../../services/studentService';

export default function EnrolledStudentsModal({ isOpen, onClose, subject, canManage = false }) {
  const [enrolledStudents, setEnrolledStudents] = useState([]);
  const [availableStudents, setAvailableStudents] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [loading, setLoading] = useState(false);
  const [enrolling, setEnrolling] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const fetchEnrolled = useCallback(async () => {
    if (!subject) return;
    setLoading(true);
    setError(null);
    try {
      const data = await subjectService.getEnrolledStudents(subject.id);
      setEnrolledStudents(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [subject]);

  const fetchAvailable = useCallback(async () => {
    try {
      const res = await studentService.getStudents({ size: 100 });
      setAvailableStudents(res.items || []);
    } catch {
      // Ignore if cannot load all students
    }
  }, []);

  useEffect(() => {
    if (isOpen && subject) {
      fetchEnrolled();
      if (canManage) {
        fetchAvailable();
      }
      setError(null);
      setSuccess(null);
      setSelectedStudentId('');
    }
  }, [isOpen, subject, canManage, fetchEnrolled, fetchAvailable]);

  if (!isOpen || !subject) return null;

  const handleEnroll = async (e) => {
    e.preventDefault();
    if (!selectedStudentId) return;

    setEnrolling(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await subjectService.enrollStudents(subject.id, [Number(selectedStudentId)], subject.academic_year);
      setSuccess(res.message);
      setSelectedStudentId('');
      fetchEnrolled();
    } catch (err) {
      setError(err.message);
    } finally {
      setEnrolling(false);
    }
  };

  const handleUnenroll = async (studentId) => {
    try {
      await subjectService.unenrollStudent(subject.id, studentId);
      setSuccess('Student unenrolled successfully.');
      fetchEnrolled();
    } catch (err) {
      setError(err.message);
    }
  };

  // Filter out students who are already enrolled
  const enrolledIds = new Set(enrolledStudents.map((s) => s.student_id));
  const candidateStudents = availableStudents.filter((s) => !enrolledIds.has(s.id));

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog" style={{ maxWidth: '720px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div className="sm-icon-badge" style={{ width: '40px', height: '40px' }}>
              <Users size={20} />
            </div>
            <div>
              <h3>Enrolled Students Roster</h3>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>
                {subject.code} — {subject.name} ({subject.academic_year})
              </p>
            </div>
          </div>
          <button type="button" className="icon-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div style={{ padding: '1.25rem 1.5rem' }}>
          {error && (
            <div className="modal-alert-error" style={{ margin: '0 0 1rem 0' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="toast-banner toast-success" style={{ margin: '0 0 1rem 0', padding: '0.65rem 1rem' }}>
              <div className="toast-content">
                <CheckCircle2 size={18} />
                <span>{success}</span>
              </div>
            </div>
          )}

          {/* Quick Enroll Bar (Lecturers / Admins) */}
          {canManage && (
            <form onSubmit={handleEnroll} style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <select
                className="filter-select"
                value={selectedStudentId}
                onChange={(e) => setSelectedStudentId(e.target.value)}
                style={{ flex: 1 }}
                required
              >
                <option value="">Select a student to enroll...</option>
                {candidateStudents.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.student_id_number} - {s.first_name} {s.last_name} ({s.department})
                  </option>
                ))}
              </select>
              <button
                type="submit"
                className="btn-primary"
                disabled={enrolling || !selectedStudentId}
                style={{ whiteSpace: 'nowrap' }}
              >
                <UserPlus size={16} />
                <span>{enrolling ? 'Enrolling...' : 'Enroll Student'}</span>
              </button>
            </form>
          )}

          {/* Enrolled Students Table */}
          <div style={{ maxHeight: '380px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
            <table className="students-table" style={{ margin: 0 }}>
              <thead>
                <tr>
                  <th>Student ID</th>
                  <th>Student Name</th>
                  <th>Department & Class</th>
                  <th>Enrolled On</th>
                  {canManage && <th style={{ textAlign: 'right' }}>Action</th>}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={canManage ? 5 : 4} style={{ textAlign: 'center', padding: '2rem' }}>
                      <div className="spinner" style={{ width: '24px', height: '24px' }} />
                      <span>Loading enrolled students...</span>
                    </td>
                  </tr>
                ) : enrolledStudents.length === 0 ? (
                  <tr>
                    <td colSpan={canManage ? 5 : 4} style={{ textAlign: 'center', padding: '2.5rem', color: '#64748b' }}>
                      No students are currently enrolled in this subject.
                    </td>
                  </tr>
                ) : (
                  enrolledStudents.map((item) => (
                    <tr key={item.enrollment_id}>
                      <td className="student-id-cell">{item.student_id_number}</td>
                      <td>
                        <strong>
                          {item.first_name} {item.last_name}
                        </strong>
                        <div className="email-sub">{item.email}</div>
                      </td>
                      <td>
                        {item.department} • <span style={{ color: '#6366f1' }}>{item.class_name}</span>
                      </td>
                      <td style={{ fontSize: '0.82rem', color: '#64748b' }}>
                        {new Date(item.enrolled_at).toLocaleDateString()}
                      </td>
                      {canManage && (
                        <td style={{ textAlign: 'right' }}>
                          <button
                            type="button"
                            className="btn-icon-action delete"
                            onClick={() => handleUnenroll(item.student_id)}
                            title="Unenroll student from subject"
                          >
                            <Trash2 size={16} />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
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
