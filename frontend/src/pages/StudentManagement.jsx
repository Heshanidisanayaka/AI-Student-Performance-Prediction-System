import React, { useState, useEffect, useCallback } from 'react';
import {
  GraduationCap,
  Plus,
  Search,
  Filter,
  RefreshCw,
  Eye,
  Edit,
  Trash2,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  CheckCircle2,
  AlertCircle,
  X,
  Shield,
  UserCheck,
} from 'lucide-react';
import { studentService } from '../services/studentService';
import { authService } from '../services/authService';
import StudentModal from '../components/StudentManagement/StudentModal';
import DeleteConfirmModal from '../components/StudentManagement/DeleteConfirmModal';
import StudentDetailModal from '../components/StudentManagement/StudentDetailModal';
import './StudentManagement.css';

export default function StudentManagement() {
  // Authentication & Demo User State
  const [currentUser, setCurrentUser] = useState(authService.getStoredUser());
  const [currentRole, setCurrentRole] = useState(currentUser?.role || 'admin');

  // Students Table State
  const [students, setStudents] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, size: 8, total: 0, pages: 1 });
  const [loading, setLoading] = useState(false);

  // Search & Filter State
  const [searchTerm, setSearchTerm] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Notification State
  const [toast, setToast] = useState(null);

  // Modals State
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [formInitialData, setFormInitialData] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  const [detailStudent, setDetailStudent] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const [studentToDelete, setStudentToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 5000);
  };

  // Switch demo roles seamlessly for university evaluation
  const handleRoleSwitch = async (newRole) => {
    setLoading(true);
    try {
      let email = 'system_admin@university.edu';
      let password = 'AdminPass2026!';

      if (newRole === 'lecturer') {
        email = 'lecturer_crud@university.edu';
        password = 'LecturerPass2026!';
      } else if (newRole === 'student') {
        // Try logging in as student or fallback
        email = 'student1@university.edu';
        password = 'Password123!';
      }

      const { user } = await authService.login(email, password);
      setCurrentUser(user);
      setCurrentRole(user.role);
      showToast('success', `Switched session to ${user.role.toUpperCase()} (${user.email})`);
    } catch (err) {
      showToast('error', `Failed to authenticate as ${newRole}: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Fetch Students
  const fetchStudents = useCallback(async () => {
    setLoading(true);
    try {
      // Ensure we have an active session
      if (!authService.getStoredToken()) {
        await authService.login('system_admin@university.edu', 'AdminPass2026!');
      }

      const data = await studentService.getStudents({
        page: pagination.page,
        size: pagination.size,
        search: searchTerm,
        department: departmentFilter,
        status: statusFilter,
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      setStudents(data.items || []);
      setPagination((prev) => ({
        ...prev,
        total: data.total,
        pages: data.pages,
      }));
    } catch (err) {
      showToast('error', `Error loading students: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.size, searchTerm, departmentFilter, statusFilter, sortBy, sortOrder]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  // Handle Create or Update Student Submit
  const handleFormSubmit = async (formData) => {
    setIsSubmitting(true);
    setFormError(null);
    try {
      if (formInitialData) {
        // Update
        const updated = await studentService.updateStudent(formInitialData.id, formData);
        showToast('success', `Student '${updated.student_id_number}' updated successfully.`);
      } else {
        // Create
        const created = await studentService.createStudent(formData);
        showToast('success', `Student '${created.student_id_number}' created successfully.`);
      }
      setIsFormModalOpen(false);
      setFormInitialData(null);
      fetchStudents();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Open Edit Modal
  const handleOpenEdit = (student) => {
    setFormInitialData(student);
    setFormError(null);
    setIsFormModalOpen(true);
  };

  // Open View Detail Modal
  const handleOpenDetail = async (studentId) => {
    try {
      const data = await studentService.getStudentById(studentId);
      setDetailStudent(data);
      setIsDetailModalOpen(true);
    } catch (err) {
      showToast('error', `Could not load student profile: ${err.message}`);
    }
  };

  // Handle Delete Confirmation
  const handleDeleteConfirm = async (studentId) => {
    setIsDeleting(true);
    try {
      const res = await studentService.deleteStudent(studentId);
      showToast('success', res.message || 'Student deleted successfully.');
      setStudentToDelete(null);
      fetchStudents();
    } catch (err) {
      showToast('error', `Delete failed: ${err.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  // Toggle Sorting
  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

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

  const canModify = currentRole === 'admin' || currentRole === 'lecturer';
  const canDelete = currentRole === 'admin';

  return (
    <div className="sm-container">
      {/* Top Header */}
      <header className="sm-header">
        <div className="sm-title-group">
          <div className="sm-icon-badge">
            <GraduationCap size={28} />
          </div>
          <div>
            <h1>Student Management</h1>
            <p>Real-Time Academic Registry, Profiles & Risk Monitoring</p>
          </div>
        </div>

        <div className="sm-header-actions">
          {/* Quick Role Simulator Switcher for Evaluation */}
          <div className={`user-badge-pill ${currentRole}`}>
            <Shield size={15} />
            <span>Role:</span>
            <select
              value={currentRole}
              onChange={(e) => handleRoleSwitch(e.target.value)}
              className="role-select"
              title="Switch role to evaluate RBAC restrictions"
            >
              <option value="admin">Admin (Full Access)</option>
              <option value="lecturer">Lecturer (CRUD except Delete)</option>
              <option value="student">Student (Read Own Only)</option>
            </select>
          </div>

          <button
            type="button"
            className="btn-secondary"
            onClick={fetchStudents}
            disabled={loading}
            title="Refresh Registry"
          >
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
          </button>

          {canModify && (
            <button
              type="button"
              className="btn-primary"
              onClick={() => {
                setFormInitialData(null);
                setFormError(null);
                setIsFormModalOpen(true);
              }}
            >
              <Plus size={18} />
              <span>Add Student</span>
            </button>
          )}
        </div>
      </header>

      {/* Toast Alert Banner */}
      {toast && (
        <div className={`toast-banner toast-${toast.type}`}>
          <div className="toast-content">
            {toast.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
            <span>{toast.message}</span>
          </div>
          <button type="button" className="icon-btn" onClick={() => setToast(null)}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Toolbar: Search, Filters & Stats */}
      <div className="toolbar-card">
        <div className="toolbar-grid">
          <div className="search-input-wrapper">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by student name, ID number, or email..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPagination((p) => ({ ...p, page: 1 }));
              }}
            />
          </div>

          <select
            className="filter-select"
            value={departmentFilter}
            onChange={(e) => {
              setDepartmentFilter(e.target.value);
              setPagination((p) => ({ ...p, page: 1 }));
            }}
          >
            <option value="">All Departments</option>
            <option value="Computer Science">Computer Science</option>
            <option value="Information Technology">Information Technology</option>
            <option value="Data Science">Data Science</option>
            <option value="Software Engineering">Software Engineering</option>
            <option value="Cybernetics">Cybernetics</option>
          </select>

          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPagination((p) => ({ ...p, page: 1 }));
            }}
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="at_risk">At Risk</option>
            <option value="graduated">Graduated</option>
            <option value="suspended">Suspended</option>
          </select>

          <button
            type="button"
            className="btn-secondary"
            onClick={() => {
              setSearchTerm('');
              setDepartmentFilter('');
              setStatusFilter('');
            }}
          >
            Reset Filters
          </button>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="table-card">
        <div className="table-responsive">
          <table className="students-table">
            <thead>
              <tr>
                <th className="sortable-th" onClick={() => handleSort('student_id_number')}>
                  <div className="th-content">
                    <span>Student ID</span>
                    <ArrowUpDown size={14} />
                  </div>
                </th>
                <th className="sortable-th" onClick={() => handleSort('first_name')}>
                  <div className="th-content">
                    <span>Student Details</span>
                    <ArrowUpDown size={14} />
                  </div>
                </th>
                <th>Department & Class</th>
                <th className="sortable-th" onClick={() => handleSort('current_semester')}>
                  <div className="th-content">
                    <span>Semester</span>
                    <ArrowUpDown size={14} />
                  </div>
                </th>
                <th className="sortable-th" onClick={() => handleSort('status')}>
                  <div className="th-content">
                    <span>Academic Status</span>
                    <ArrowUpDown size={14} />
                  </div>
                </th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading && students.length === 0 ? (
                <tr>
                  <td colSpan="6">
                    <div className="state-box">
                      <div className="spinner" />
                      <p>Loading student directory...</p>
                    </div>
                  </td>
                </tr>
              ) : students.length === 0 ? (
                <tr>
                  <td colSpan="6">
                    <div className="state-box">
                      <GraduationCap size={42} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
                      <h4>No Students Found</h4>
                      <p>Try adjusting your search query or department filter.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                students.map((student) => (
                  <tr key={student.id}>
                    <td className="student-id-cell">{student.student_id_number}</td>
                    <td>
                      <div className="student-name-cell">
                        <div className="avatar-badge">
                          {student.first_name?.[0]}
                          {student.last_name?.[0]}
                        </div>
                        <div>
                          <div className="name-primary">
                            {student.first_name} {student.last_name}
                          </div>
                          <div className="email-sub">{student.email}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div>
                        <strong>{student.department}</strong>
                        <div className="email-sub">
                          {student.class_name} • {student.academic_year}
                        </div>
                      </div>
                    </td>
                    <td>Semester {student.current_semester}</td>
                    <td>{getStatusBadge(student.status)}</td>
                    <td>
                      <div className="action-buttons-cell" style={{ justifyContent: 'flex-end' }}>
                        <button
                          type="button"
                          className="btn-icon-action"
                          onClick={() => handleOpenDetail(student.id)}
                          title="View Profile Details"
                        >
                          <Eye size={16} />
                        </button>

                        {canModify && (
                          <button
                            type="button"
                            className="btn-icon-action"
                            onClick={() => handleOpenEdit(student)}
                            title="Edit Student Record"
                          >
                            <Edit size={16} />
                          </button>
                        )}

                        {canDelete && (
                          <button
                            type="button"
                            className="btn-icon-action delete"
                            onClick={() => setStudentToDelete(student)}
                            title="Delete Student"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="pagination-bar">
          <div>
            Showing <strong>{students.length}</strong> of <strong>{pagination.total}</strong> registered students
          </div>
          <div className="pagination-controls">
            <button
              type="button"
              className="page-btn"
              disabled={pagination.page <= 1 || loading}
              onClick={() => setPagination((p) => ({ ...p, page: p.page - 1 }))}
            >
              <ChevronLeft size={16} />
              <span>Previous</span>
            </button>
            <span>
              Page <strong>{pagination.page}</strong> of <strong>{pagination.pages || 1}</strong>
            </span>
            <button
              type="button"
              className="page-btn"
              disabled={pagination.page >= pagination.pages || loading}
              onClick={() => setPagination((p) => ({ ...p, page: p.page + 1 }))}
            >
              <span>Next</span>
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Add / Edit Student Modal */}
      <StudentModal
        isOpen={isFormModalOpen}
        onClose={() => {
          setIsFormModalOpen(false);
          setFormInitialData(null);
          setFormError(null);
        }}
        onSubmit={handleFormSubmit}
        initialData={formInitialData}
        isSubmitting={isSubmitting}
        error={formError}
      />

      {/* View Detail Modal */}
      <StudentDetailModal
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false);
          setDetailStudent(null);
        }}
        student={detailStudent}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={Boolean(studentToDelete)}
        onClose={() => setStudentToDelete(null)}
        onConfirm={handleDeleteConfirm}
        student={studentToDelete}
        isDeleting={isDeleting}
      />
    </div>
  );
}
