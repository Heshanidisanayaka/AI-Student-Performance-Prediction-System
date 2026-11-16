import React, { useState, useEffect } from 'react';
import { X, Award, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { attendanceService } from '../../services/attendanceService';

export default function StudentStatsModal({ isOpen, onClose, studentId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchStats = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await attendanceService.getStudentStats(studentId);
        setData(res);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to fetch student attendance statistics.');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [studentId]);

  if (!isOpen) return null;

  const stats = data?.overall_stats;
  const isSatisfactory = (stats?.attendance_percentage ?? 0) >= 75;

  return (
    <div className="modal-backdrop">
      <div className="modal-content attendance-stats-modal">
        <div className="modal-header">
          <div>
            <h3>Student Attendance Profile</h3>
            <p className="modal-subtitle">
              {data ? `${data.student_name} (${data.student_id_number})` : 'Loading profile...'}
            </p>
          </div>
          <button type="button" className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {error && <div className="modal-error-banner">{error}</div>}

        {loading ? (
          <div className="stats-modal-loading">
            <span className="spinner-sm"></span> Loading attendance metrics...
          </div>
        ) : data ? (
          <div className="stats-modal-body">
            {/* Policy Info Callout */}
            <div className="policy-callout">
              <Info size={18} className="policy-icon" />
              <div className="policy-text">
                <strong>Institutional Excused Absence Policy:</strong>
                <p>
                  Excused absences do not penalize the student and are excluded from the denominator:
                  <code> Attendance % = Present / (Total Sessions - Excused) × 100</code>.
                </p>
              </div>
            </div>

            {/* KPI Cards */}
            <div className="stats-kpi-grid">
              <div className={`stats-kpi-card ${isSatisfactory ? 'kpi-success' : 'kpi-danger'}`}>
                <span className="kpi-label">Overall Percentage</span>
                <span className="kpi-value">{stats?.attendance_percentage ?? 0}%</span>
                <span className="kpi-subtext">
                  {isSatisfactory ? (
                    <span className="text-success"><CheckCircle size={14} /> Meets 75% Requirement</span>
                  ) : (
                    <span className="text-danger"><AlertTriangle size={14} /> Below 75% Threshold</span>
                  )}
                </span>
              </div>

              <div className="stats-kpi-card">
                <span className="kpi-label">Total Sessions</span>
                <span className="kpi-value">{stats?.total_sessions ?? 0}</span>
                <span className="kpi-subtext">Registered class sessions</span>
              </div>

              <div className="stats-kpi-card">
                <span className="kpi-label">Present Sessions</span>
                <span className="kpi-value text-success">{stats?.present_count ?? 0}</span>
                <span className="kpi-subtext">Attended</span>
              </div>

              <div className="stats-kpi-card">
                <span className="kpi-label">Excused Absences</span>
                <span className="kpi-value text-amber">{stats?.excused_count ?? 0}</span>
                <span className="kpi-subtext">Non-penalized</span>
              </div>

              <div className="stats-kpi-card">
                <span className="kpi-label">Unexcused Absences</span>
                <span className="kpi-value text-danger">{stats?.absent_count ?? 0}</span>
                <span className="kpi-subtext">Penalized absences</span>
              </div>
            </div>

            {/* Subject Breakdown Table */}
            <div className="stats-subject-section">
              <h4>Subject-wise Attendance Breakdown</h4>
              {data.subject_breakdown.length === 0 ? (
                <p className="empty-subtext">No attendance entries recorded for any subjects yet.</p>
              ) : (
                <div className="stats-table-wrapper">
                  <table className="stats-table">
                    <thead>
                      <tr>
                        <th>Subject</th>
                        <th>Total</th>
                        <th>Present</th>
                        <th>Excused</th>
                        <th>Absent</th>
                        <th>Effective</th>
                        <th>Attendance %</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.subject_breakdown.map((item) => {
                        const subPct = item.stats.attendance_percentage;
                        const subOk = subPct >= 75;
                        return (
                          <tr key={item.subject_id}>
                            <td>
                              <strong>{item.subject_code}</strong>
                              <span className="sub-name-cell">{item.subject_name}</span>
                            </td>
                            <td>{item.stats.total_sessions}</td>
                            <td className="text-success">{item.stats.present_count}</td>
                            <td className="text-amber">{item.stats.excused_count}</td>
                            <td className="text-danger">{item.stats.absent_count}</td>
                            <td>{item.stats.effective_sessions}</td>
                            <td>
                              <strong className={subOk ? 'text-success' : 'text-danger'}>
                                {subPct}%
                              </strong>
                            </td>
                            <td>
                              <span className={`compliance-tag ${subOk ? 'tag-compliant' : 'tag-warning'}`}>
                                {subOk ? 'Eligible' : 'At Risk'}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ) : null}

        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
