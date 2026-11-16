import React, { useState, useEffect, useCallback } from 'react';
import {
  CalendarCheck,
  Plus,
  Search,
  RefreshCw,
  Edit,
  Trash2,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  X,
  Shield,
  BarChart3,
  TrendingUp,
  PieChart as PieIcon,
  Eye,
  Filter,
  Check,
  UserX,
  Clock,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';

import { attendanceService } from '../services/attendanceService';
import { subjectService } from '../services/subjectService';
import { authService } from '../services/authService';

import RecordSessionModal from '../components/AttendanceManagement/RecordSessionModal';
import EditAttendanceModal from '../components/AttendanceManagement/EditAttendanceModal';
import StudentStatsModal from '../components/AttendanceManagement/StudentStatsModal';
import DeleteConfirmModal from '../components/StudentManagement/DeleteConfirmModal';

import './AttendanceManagement.css';

const PIE_COLORS = {
  Present: '#10b981',
  Absent: '#ef4444',
  Excused: '#f59e0b',
};

export default function AttendanceManagement() {
  const [currentUser, setCurrentUser] = useState(authService.getStoredUser());
  const [currentRole, setCurrentRole] = useState(currentUser?.role || 'lecturer');

  // Attendance Records State
  const [records, setRecords] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, size: 15, total: 0, pages: 1 });
  const [loading, setLoading] = useState(false);

  // Available subjects for dropdowns
  const [subjectsList, setSubjectsList] = useState([]);

  // Search & Filter state
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sessionFilter, setSessionFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Analytics & Visualizations State
  const [showAnalytics, setShowAnalytics] = useState(true);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);

  // Modals state
  const [isRecordModalOpen, setIsRecordModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [statsStudentId, setStatsStudentId] = useState(null);
  const [recordToDelete, setRecordToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Notifications
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Fetch subjects for dropdown selection
  useEffect(() => {
    const loadSubjects = async () => {
      try {
        const res = await subjectService.getSubjects({ size: 100 });
        setSubjectsList(res.items || []);
      } catch (err) {
        console.error('Failed to load subjects list:', err);
      }
    };
    loadSubjects();
  }, []);

  // Fetch Attendance Records
  const fetchAttendance = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.page,
        size: pagination.size,
        subject_id: selectedSubjectId ? parseInt(selectedSubjectId, 10) : undefined,
        status: statusFilter || undefined,
        session_name: sessionFilter || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      };

      const data = await attendanceService.getAttendanceRecords(params);
      setRecords(data.items || []);
      setPagination((prev) => ({
        ...prev,
        total: data.total,
        pages: data.pages || 1,
      }));
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to fetch attendance records.', 'error');
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.size, selectedSubjectId, statusFilter, sessionFilter, startDate, endDate]);

  // Fetch Analytics Data for Recharts
  const fetchAnalytics = useCallback(async () => {
    if (currentRole === 'student') return;
    setLoadingAnalytics(true);
    try {
      const data = await attendanceService.getAttendanceAnalytics(
        selectedSubjectId ? parseInt(selectedSubjectId, 10) : null
      );
      setAnalyticsData(data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      setLoadingAnalytics(false);
    }
  }, [selectedSubjectId, currentRole]);

  useEffect(() => {
    fetchAttendance();
  }, [fetchAttendance]);

  useEffect(() => {
    if (showAnalytics) {
      fetchAnalytics();
    }
  }, [showAnalytics, fetchAnalytics]);

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.pages) {
      setPagination((prev) => ({ ...prev, page: newPage }));
    }
  };

  const handleResetFilters = () => {
    setSelectedSubjectId('');
    setStatusFilter('');
    setSessionFilter('');
    setStartDate('');
    setEndDate('');
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handleDeleteConfirm = async () => {
    if (!recordToDelete) return;
    setIsDeleting(true);
    try {
      await attendanceService.deleteAttendance(recordToDelete.id);
      showToast('Attendance record deleted successfully.');
      setRecordToDelete(null);
      fetchAttendance();
      fetchAnalytics();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to delete record.', 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  const canManage = currentRole === 'admin' || currentRole === 'lecturer';

  return (
    <div className="attendance-page-container">
      {/* Toast Notification */}
      {toast && (
        <div className={`toast-notification toast-${toast.type}`}>
          {toast.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span>{toast.message}</span>
          <button type="button" className="toast-close" onClick={() => setToast(null)}>
            <X size={14} />
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="page-header-card">
        <div className="header-left">
          <div className="header-icon-box">
            <CalendarCheck size={28} color="#fff" />
          </div>
          <div>
            <h1 className="page-title">Student Attendance Tracking</h1>
            <p className="page-subtitle">
              Session-based attendance marking, institutional excused absence policy calculations, and Recharts analytics.
            </p>
          </div>
        </div>

        <div className="header-actions">
          {/* Role Indicator / Switcher for previewing permissions */}
          <div className="role-badge-selector">
            <Shield size={14} />
            <select
              value={currentRole}
              onChange={(e) => setCurrentRole(e.target.value)}
              className="role-select"
            >
              <option value="admin">Role: Admin</option>
              <option value="lecturer">Role: Lecturer</option>
              <option value="student">Role: Student</option>
            </select>
          </div>

          <button
            type="button"
            className={`btn-toggle-analytics ${showAnalytics ? 'active' : ''}`}
            onClick={() => setShowAnalytics(!showAnalytics)}
            title="Toggle Analytics Charts"
          >
            <BarChart3 size={16} />
            <span>{showAnalytics ? 'Hide Analytics' : 'Show Analytics'}</span>
          </button>

          {canManage && (
            <button
              type="button"
              className="btn-primary"
              onClick={() => setIsRecordModalOpen(true)}
            >
              <Plus size={16} />
              <span>Record Session</span>
            </button>
          )}

          <button
            type="button"
            className="btn-icon-refresh"
            onClick={() => {
              fetchAttendance();
              fetchAnalytics();
            }}
            title="Refresh Attendance Data"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Institutional Policy Banner */}
      <div className="institutional-policy-banner">
        <Info size={20} className="banner-icon" />
        <div className="banner-content">
          <strong>Institutional Excused Absence Policy:</strong>
          <span>
            Excused absences do not penalize students and are excluded from the denominator:
            <code> Attendance % = Present / (Total Sessions - Excused) × 100</code>.
            Minimum required threshold for examination eligibility is <strong>75%</strong>.
          </span>
        </div>
      </div>

      {/* Analytics Dashboard (Recharts Visualizations) */}
      {showAnalytics && (
        <div className="analytics-section">
          {loadingAnalytics ? (
            <div className="analytics-loading">
              <span className="spinner-sm"></span> Loading attendance visualizations...
            </div>
          ) : analyticsData ? (
            <>
              {/* Summary Metric Cards */}
              <div className="analytics-metric-grid">
                <div className="metric-card">
                  <span className="metric-label">Total Sessions Tracked</span>
                  <span className="metric-value">{analyticsData.overall_stats.total_sessions}</span>
                  <span className="metric-desc">Across all monitored sessions</span>
                </div>
                <div className="metric-card metric-success">
                  <span className="metric-label">Overall Attendance Rate</span>
                  <span className="metric-value">{analyticsData.overall_stats.attendance_percentage}%</span>
                  <span className="metric-desc">Excused absences excluded</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Present Records</span>
                  <span className="metric-value text-success">{analyticsData.overall_stats.present_count}</span>
                  <span className="metric-desc">Attended on time</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Excused Absences</span>
                  <span className="metric-value text-amber">{analyticsData.overall_stats.excused_count}</span>
                  <span className="metric-desc">Approved non-penalized</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Unexcused Absences</span>
                  <span className="metric-value text-danger">{analyticsData.overall_stats.absent_count}</span>
                  <span className="metric-desc">Penalized absences</span>
                </div>
              </div>

              {/* Recharts Grid */}
              <div className="charts-grid">
                {/* Chart 1: Subject Attendance Comparison (Bar Chart) */}
                <div className="chart-card">
                  <div className="chart-header">
                    <h4>
                      <BarChart3 size={18} /> Subject Attendance vs 75% Requirement
                    </h4>
                    <span className="chart-subtitle">Threshold: 75% minimum institutional standard</span>
                  </div>
                  <div className="chart-body">
                    {analyticsData.subject_comparisons.length === 0 ? (
                      <p className="no-chart-data">No subject data available for visualization.</p>
                    ) : (
                      <ResponsiveContainer width="100%" height={260}>
                        <BarChart
                          data={analyticsData.subject_comparisons}
                          margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                          <XAxis dataKey="subject_code" stroke="#94a3b8" />
                          <YAxis domain={[0, 100]} stroke="#94a3b8" unit="%" />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                            formatter={(value) => [`${value}%`, 'Attendance Rate']}
                          />
                          <ReferenceLine
                            y={75}
                            stroke="#f59e0b"
                            strokeDasharray="4 4"
                            label={{ value: '75% Threshold', fill: '#f59e0b', position: 'top' }}
                          />
                          <Bar dataKey="percentage" name="Attendance %" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                            {analyticsData.subject_comparisons.map((entry, index) => (
                              <Cell
                                key={`cell-${index}`}
                                fill={entry.percentage >= 75 ? '#10b981' : '#ef4444'}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </div>

                {/* Chart 2: Status Distribution (Pie Chart) */}
                <div className="chart-card">
                  <div className="chart-header">
                    <h4>
                      <PieIcon size={18} /> Attendance Status Distribution
                    </h4>
                    <span className="chart-subtitle">Proportion of Present, Absent, and Excused entries</span>
                  </div>
                  <div className="chart-body">
                    <ResponsiveContainer width="100%" height={260}>
                      <PieChart>
                        <Pie
                          data={analyticsData.status_distribution}
                          cx="50%"
                          cy="50%"
                          innerRadius={55}
                          outerRadius={90}
                          paddingAngle={4}
                          dataKey="value"
                        >
                          {analyticsData.status_distribution.map((entry, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={PIE_COLORS[entry.name] || '#64748b'}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                        />
                        <Legend verticalAlign="bottom" height={36} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Chart 3: Daily Attendance Trend (Line Chart) */}
                <div className="chart-card chart-span-full">
                  <div className="chart-header">
                    <h4>
                      <TrendingUp size={18} /> Daily Attendance Trends Over Time
                    </h4>
                    <span className="chart-subtitle">Daily student attendance percentage progression</span>
                  </div>
                  <div className="chart-body">
                    {analyticsData.daily_trends.length === 0 ? (
                      <p className="no-chart-data">No daily session trend data available yet.</p>
                    ) : (
                      <ResponsiveContainer width="100%" height={240}>
                        <LineChart
                          data={analyticsData.daily_trends}
                          margin={{ top: 10, right: 30, left: 0, bottom: 10 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                          <XAxis dataKey="date" stroke="#94a3b8" />
                          <YAxis domain={[0, 100]} stroke="#94a3b8" unit="%" />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                            formatter={(value) => [`${value}%`, 'Attendance Rate']}
                          />
                          <Line
                            type="monotone"
                            dataKey="percentage"
                            stroke="#10b981"
                            strokeWidth={3}
                            dot={{ fill: '#10b981', r: 4 }}
                            activeDot={{ r: 6 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* Filter and Query Toolbar */}
      <div className="filters-card">
        <div className="filter-group">
          <label>Subject Filter</label>
          <select
            value={selectedSubjectId}
            onChange={(e) => {
              setSelectedSubjectId(e.target.value);
              setPagination((prev) => ({ ...prev, page: 1 }));
            }}
          >
            <option value="">All Subjects</option>
            {subjectsList.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code} - {s.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Status Filter</label>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPagination((prev) => ({ ...prev, page: 1 }));
            }}
          >
            <option value="">All Statuses</option>
            <option value="present">Present</option>
            <option value="absent">Absent</option>
            <option value="excused">Excused</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Session Name</label>
          <input
            type="text"
            placeholder="e.g. Session 1, Lab"
            value={sessionFilter}
            onChange={(e) => {
              setSessionFilter(e.target.value);
              setPagination((prev) => ({ ...prev, page: 1 }));
            }}
          />
        </div>

        <div className="filter-group">
          <label>From Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPagination((prev) => ({ ...prev, page: 1 }));
            }}
          />
        </div>

        <div className="filter-group">
          <label>To Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPagination((prev) => ({ ...prev, page: 1 }));
            }}
          />
        </div>

        <div className="filter-actions-box">
          <button type="button" className="btn-reset" onClick={handleResetFilters}>
            Reset Filters
          </button>
        </div>
      </div>

      {/* Attendance History Table */}
      <div className="table-card">
        <div className="table-header-row">
          <h3>
            Attendance Records History <span className="badge-count">({pagination.total})</span>
          </h3>
          <span className="table-note">
            Showing page {pagination.page} of {pagination.pages}
          </span>
        </div>

        {loading ? (
          <div className="table-loading-box">
            <span className="spinner-sm"></span> Loading attendance logs...
          </div>
        ) : records.length === 0 ? (
          <div className="table-empty-box">
            <CalendarCheck size={40} className="empty-icon" />
            <p>No attendance records match your active search filters.</p>
            {canManage && (
              <button
                type="button"
                className="btn-primary"
                onClick={() => setIsRecordModalOpen(true)}
              >
                Record First Session
              </button>
            )}
          </div>
        ) : (
          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Date & Session</th>
                  <th>Student</th>
                  <th>Subject</th>
                  <th>Status</th>
                  <th>Remarks / Excuse</th>
                  <th>Recorded By</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <div className="date-session-cell">
                        <span className="record-date">{r.date}</span>
                        <span className="record-session-tag">{r.session_name}</span>
                      </div>
                    </td>
                    <td>
                      <div className="student-profile-link">
                        <button
                          type="button"
                          className="btn-student-name"
                          onClick={() => setStatsStudentId(r.student_id)}
                          title="View Attendance Breakdown"
                        >
                          {r.student_name}
                        </button>
                        <span className="student-id-sub">{r.student_id_number}</span>
                      </div>
                    </td>
                    <td>
                      <div className="subject-cell">
                        <span className="subject-code-tag">{r.subject_code}</span>
                        <span className="subject-name-sub">{r.subject_name}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge badge-${r.status.toLowerCase()}`}>
                        {r.status.charAt(0).toUpperCase() + r.status.slice(1)}
                      </span>
                    </td>
                    <td>
                      <span className="remarks-cell">
                        {r.remarks || <span className="empty-remark">—</span>}
                      </span>
                    </td>
                    <td>
                      <span className="recorder-name">
                        {r.recorded_by_name || 'System / Faculty'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div className="table-actions-cell">
                        <button
                          type="button"
                          className="btn-action-icon"
                          onClick={() => setStatsStudentId(r.student_id)}
                          title="View Student Attendance Statistics"
                        >
                          <Eye size={16} />
                        </button>
                        {canManage && (
                          <>
                            <button
                              type="button"
                              className="btn-action-icon"
                              onClick={() => setEditingRecord(r)}
                              title="Update Status / Add Excuse"
                            >
                              <Edit size={16} />
                            </button>
                            <button
                              type="button"
                              className="btn-action-icon btn-action-danger"
                              onClick={() => setRecordToDelete(r)}
                              title="Delete Erroneous Record"
                            >
                              <Trash2 size={16} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls */}
        {pagination.pages > 1 && (
          <div className="pagination-bar">
            <span className="pagination-info">
              Showing {(pagination.page - 1) * pagination.size + 1} to{' '}
              {Math.min(pagination.page * pagination.size, pagination.total)} of{' '}
              {pagination.total} records
            </span>
            <div className="pagination-nav">
              <button
                type="button"
                className="btn-page"
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={pagination.page <= 1}
              >
                <ChevronLeft size={16} /> Previous
              </button>
              <span className="current-page-tag">
                {pagination.page} / {pagination.pages}
              </span>
              <button
                type="button"
                className="btn-page"
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={pagination.page >= pagination.pages}
              >
                Next <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Record Session Attendance Modal */}
      <RecordSessionModal
        isOpen={isRecordModalOpen}
        onClose={() => setIsRecordModalOpen(false)}
        subjects={subjectsList}
        onSuccess={(msg) => {
          showToast(msg);
          fetchAttendance();
          fetchAnalytics();
        }}
      />

      {/* Edit Record Modal */}
      <EditAttendanceModal
        isOpen={!!editingRecord}
        record={editingRecord}
        onClose={() => setEditingRecord(null)}
        onSuccess={(msg) => {
          showToast(msg);
          fetchAttendance();
          fetchAnalytics();
        }}
      />

      {/* Student Stats Modal */}
      <StudentStatsModal
        isOpen={!!statsStudentId}
        studentId={statsStudentId}
        onClose={() => setStatsStudentId(null)}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={!!recordToDelete}
        onClose={() => setRecordToDelete(null)}
        onConfirm={handleDeleteConfirm}
        isDeleting={isDeleting}
        title="Delete Attendance Record"
        message={`Are you sure you want to delete the attendance record for student ${recordToDelete?.student_name} (${recordToDelete?.session_name} on ${recordToDelete?.date})?`}
      />
    </div>
  );
}
