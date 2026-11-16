import React, { useState, useEffect, useCallback } from 'react';
import {
  BookOpen,
  Plus,
  Search,
  RefreshCw,
  Users,
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
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';
import { subjectService } from '../services/subjectService';
import { authService } from '../services/authService';
import SubjectModal from '../components/SubjectManagement/SubjectModal';
import EnrolledStudentsModal from '../components/SubjectManagement/EnrolledStudentsModal';
import AssignLecturerModal from '../components/SubjectManagement/AssignLecturerModal';
import DeleteConfirmModal from '../components/StudentManagement/DeleteConfirmModal';
import './StudentManagement.css';

export default function SubjectManagement() {
  const [currentUser, setCurrentUser] = useState(authService.getStoredUser());
  const [currentRole, setCurrentRole] = useState(currentUser?.role || 'admin');

  // Subjects Table State
  const [subjects, setSubjects] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, size: 8, total: 0, pages: 1 });
  const [loading, setLoading] = useState(false);

  // Search & Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const [semesterFilter, setSemesterFilter] = useState('');
  const [mySubjectsOnly, setMySubjectsOnly] = useState(false);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Notifications
  const [toast, setToast] = useState(null);

  // Modals
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [formInitialData, setFormInitialData] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  const [selectedSubjectForRoster, setSelectedSubjectForRoster] = useState(null);
  const [selectedSubjectForLecturer, setSelectedSubjectForLecturer] = useState(null);
  const [isAssigning, setIsAssigning] = useState(false);

  const [subjectToDelete, setSubjectToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 5000);
  };

  // Demo Role Switcher
  const handleRoleSwitch = async (newRole) => {
    setLoading(true);
    try {
      let email = 'system_admin@university.edu';
      let password = 'AdminPass2026!';

      if (newRole === 'lecturer') {
        email = 'lecturer_crud@university.edu';
        password = 'LecturerPass2026!';
      } else if (newRole === 'student') {
        email = 'student1@university.edu';
        password = 'Password123!';
      }

      const { user } = await authService.login(email, password);
      setCurrentUser(user);
      setCurrentRole(user.role);
      showToast('success', `Switched session to ${user.role.toUpperCase()} (${user.email})`);
    } catch (err) {
      showToast('error', `Failed to switch role: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Fetch Subjects
  const fetchSubjects = useCallback(async () => {
    setLoading(true);
    try {
      if (!authService.getStoredToken()) {
        await authService.login('system_admin@university.edu', 'AdminPass2026!');
      }

      const isActParam = activeFilter === '' ? null : activeFilter === 'true';
      const semParam = semesterFilter === '' ? null : Number(semesterFilter);

      const data = await subjectService.getSubjects({
        page: pagination.page,
        size: pagination.size,
        search: searchTerm,
        department: departmentFilter,
        is_active: isActParam,
        semester: semParam,
        my_subjects_only: mySubjectsOnly,
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      setSubjects(data.items || []);
      setPagination((p) => ({ ...p, total: data.total, pages: data.pages }));
    } catch (err) {
      showToast('error', `Error loading subjects: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.size, searchTerm, departmentFilter, activeFilter, semesterFilter, mySubjectsOnly, sortBy, sortOrder]);

  useEffect(() => {
    fetchSubjects();
  }, [fetchSubjects]);

  // Handle Create or Edit Submit
  const handleFormSubmit = async (formData) => {
    setIsSubmitting(true);
    setFormError(null);
    try {
      if (formInitialData) {
        await subjectService.updateSubject(formInitialData.id, formData);
        showToast('success', `Subject '${formData.code}' updated successfully.`);
      } else {
        await subjectService.createSubject(formData);
        showToast('success', `Subject '${formData.code}' created successfully.`);
      }
      setIsFormModalOpen(false);
      setFormInitialData(null);
      fetchSubjects();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Deactivate / Reactivate
  const handleToggleActive = async (subject) => {
    if (currentRole !== 'admin') {
      showToast('error', 'Only administrators can activate or deactivate subjects.');
      return;
    }
    const nextState = !subject.is_active;
    try {
      await subjectService.toggleDeactivate(subject.id, nextState);
      showToast('success', `Subject '${subject.code}' ${nextState ? 'reactivated' : 'deactivated'}.`);
      fetchSubjects();
    } catch (err) {
      showToast('error', err.message);
    }
  };

  // Handle Assign Lecturer Submit
  const handleAssignLecturer = async (subjectId, lecturerId) => {
    setIsAssigning(true);
    try {
      await subjectService.assignLecturer(subjectId, lecturerId);
      showToast('success', 'Lead lecturer updated successfully.');
      setSelectedSubjectForLecturer(null);
      fetchSubjects();
    } catch (err) {
      showToast('error', err.message);
    } finally {
      setIsAssigning(false);
    }
  };

  // Handle Delete Confirmation
  const handleDeleteConfirm = async (subjectId) => {
    setIsDeleting(true);
    try {
      const res = await subjectService.deleteSubject(subjectId);
      showToast('success', res.message || 'Subject deleted successfully.');
      setSubjectToDelete(null);
      fetchSubjects();
    } catch (err) {
      showToast('error', `Delete failed: ${err.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  // Sort toggle
  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

  const isAdmin = currentRole === 'admin';
  const canManageEnrollments = currentRole === 'admin' || currentRole === 'lecturer';

  return (
    <div className="sm-container">
      {/* Header */}
      <header className="sm-header">
        <div className="sm-title-group">
          <div className="sm-icon-badge" style={{ background: 'linear-gradient(135deg, #0ea5e9, #2563eb)' }}>
            <BookOpen size={28} />
          </div>
          <div>
            <h1>Subject & Module Management</h1>
            <p>Curriculum Architecture, Faculty Assignment & Student Enrollment</p>
          </div>
        </div>

        <div className="sm-header-actions">
          {/* Role Switcher */}
          <div className={`user-badge-pill ${currentRole}`}>
            <Shield size={15} />
            <span>Role:</span>
            <select
              value={currentRole}
              onChange={(e) => handleRoleSwitch(e.target.value)}
              className="role-select"
              title="Evaluate role-based permissions"
            >
              <option value="admin">Admin (Full Control)</option>
              <option value="lecturer">Lecturer (Manage Enrollments)</option>
              <option value="student">Student (Read Enrolled)</option>
            </select>
          </div>

          <button
            type="button"
            className="btn-secondary"
            onClick={fetchSubjects}
            disabled={loading}
            title="Refresh Curriculum"
          >
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
          </button>

          {isAdmin && (
            <button
              type="button"
              className="btn-primary"
              style={{ background: '#0284c7' }}
              onClick={() => {
                setFormInitialData(null);
                setFormError(null);
                setIsFormModalOpen(true);
              }}
            >
              <Plus size={18} />
              <span>Add Subject</span>
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

      {/* Toolbar: Search, Filters & Controls */}
      <div className="toolbar-card">
        <div className="toolbar-grid">
          <div className="search-input-wrapper">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by subject code (e.g. CS101) or title..."
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
            <option value="Mathematics">Mathematics</option>
            <option value="Software Engineering">Software Engineering</option>
          </select>

          <select
            className="filter-select"
            value={activeFilter}
            onChange={(e) => {
              setActiveFilter(e.target.value);
              setPagination((p) => ({ ...p, page: 1 }));
            }}
          >
            <option value="">Offering Status (All)</option>
            <option value="true">Active Offering</option>
            <option value="false">Deactivated</option>
          </select>

          <button
            type="button"
            className="btn-secondary"
            onClick={() => {
              setSearchTerm('');
              setDepartmentFilter('');
              setActiveFilter('');
              setSemesterFilter('');
              setMySubjectsOnly(false);
            }}
          >
            Reset Filters
          </button>
        </div>
      </div>

      {/* Subjects Data Table */}
      <div className="table-card">
        <div className="table-responsive">
          <table className="students-table">
            <thead>
              <tr>
                <th className="sortable-th" onClick={() => handleSort('code')}>
                  <div className="th-content">
                    <span>Code</span>
                    <ArrowUpDown size={14} />
                  </div>
                </th>
                <th className="sortable-th" onClick={() => handleSort('name')}>
                  <div className="th-content">
                    <span>Subject / Module Details</span>
                    <ArrowUpDown size={14} />
                  </div>
                </th>
                <th>Department & Credits</th>
                <th>Lead Lecturer</th>
                <th>Enrolled Students</th>
                <th>Offering Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading && subjects.length === 0 ? (
                <tr>
                  <td colSpan="7">
                    <div className="state-box">
                      <div className="spinner" />
                      <p>Loading curriculum modules...</p>
                    </div>
                  </td>
                </tr>
              ) : subjects.length === 0 ? (
                <tr>
                  <td colSpan="7">
                    <div className="state-box">
                      <BookOpen size={42} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
                      <h4>No Subjects Found</h4>
                      <p>Try clearing your filters or create a new subject module.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                subjects.map((s) => (
                  <tr key={s.id} style={{ opacity: s.is_active ? 1 : 0.65 }}>
                    <td className="student-id-cell">
                      <span
                        style={{
                          background: '#e0f2fe',
                          color: '#0369a1',
                          padding: '0.25rem 0.55rem',
                          borderRadius: '6px',
                          fontWeight: 700,
                        }}
                      >
                        {s.code}
                      </span>
                    </td>
                    <td>
                      <div>
                        <strong style={{ color: '#0f172a' }}>{s.name}</strong>
                        {s.description && (
                          <div className="email-sub" style={{ maxWidth: '320px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {s.description}
                          </div>
                        )}
                        <div className="email-sub" style={{ marginTop: '2px' }}>
                          Academic Year: {s.academic_year}
                        </div>
                      </div>
                    </td>
                    <td>
                      <div>
                        <strong>{s.department}</strong>
                        <div className="email-sub">
                          {s.credits} Credits • Semester {s.semester}
                        </div>
                      </div>
                    </td>
                    <td>
                      {s.lecturer ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <UserCheck size={16} color="#059669" />
                          <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>{s.lecturer.full_name}</span>
                        </div>
                      ) : (
                        <span style={{ fontSize: '0.82rem', color: '#94a3b8', fontStyle: 'italic' }}>
                          Unassigned
                        </span>
                      )}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn-secondary"
                        style={{ padding: '0.3rem 0.65rem', fontSize: '0.82rem', gap: '0.35rem' }}
                        onClick={() => setSelectedSubjectForRoster(s)}
                        title="View roster of enrolled students"
                      >
                        <Users size={14} />
                        <span>
                          <strong>{s.enrolled_count}</strong> Enrolled
                        </span>
                      </button>
                    </td>
                    <td>
                      <button
                        type="button"
                        onClick={() => handleToggleActive(s)}
                        disabled={!isAdmin}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          cursor: isAdmin ? 'pointer' : 'default',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                        }}
                        title={isAdmin ? (s.is_active ? 'Click to deactivate' : 'Click to reactivate') : 'Subject Status'}
                      >
                        {s.is_active ? (
                          <>
                            <ToggleRight size={22} color="#16a34a" />
                            <span className="status-badge status-active">Active</span>
                          </>
                        ) : (
                          <>
                            <ToggleLeft size={22} color="#94a3b8" />
                            <span className="status-badge status-suspended">Deactivated</span>
                          </>
                        )}
                      </button>
                    </td>
                    <td>
                      <div className="action-buttons-cell" style={{ justifyContent: 'flex-end' }}>
                        <button
                          type="button"
                          className="btn-icon-action"
                          onClick={() => setSelectedSubjectForRoster(s)}
                          title="View Enrolled Students"
                        >
                          <Users size={16} />
                        </button>

                        {isAdmin && (
                          <>
                            <button
                              type="button"
                              className="btn-icon-action"
                              onClick={() => setSelectedSubjectForLecturer(s)}
                              title="Assign Lecturer"
                            >
                              <UserCheck size={16} />
                            </button>

                            <button
                              type="button"
                              className="btn-icon-action"
                              onClick={() => {
                                setFormInitialData(s);
                                setFormError(null);
                                setIsFormModalOpen(true);
                              }}
                              title="Edit Subject"
                            >
                              <Edit size={16} />
                            </button>

                            <button
                              type="button"
                              className="btn-icon-action delete"
                              onClick={() => setSubjectToDelete(s)}
                              title="Delete Subject"
                            >
                              <Trash2 size={16} />
                            </button>
                          </>
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
            Showing <strong>{subjects.length}</strong> of <strong>{pagination.total}</strong> subjects
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

      {/* Add / Edit Subject Modal */}
      <SubjectModal
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

      {/* Enrolled Students Roster Modal */}
      <EnrolledStudentsModal
        isOpen={Boolean(selectedSubjectForRoster)}
        onClose={() => {
          setSelectedSubjectForRoster(null);
          fetchSubjects();
        }}
        subject={selectedSubjectForRoster}
        canManage={canManageEnrollments}
      />

      {/* Assign Lecturer Modal */}
      <AssignLecturerModal
        isOpen={Boolean(selectedSubjectForLecturer)}
        onClose={() => setSelectedSubjectForLecturer(null)}
        onAssign={handleAssignLecturer}
        subject={selectedSubjectForLecturer}
        isAssigning={isAssigning}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={Boolean(subjectToDelete)}
        onClose={() => setSubjectToDelete(null)}
        onConfirm={handleDeleteConfirm}
        student={
          subjectToDelete
            ? {
                id: subjectToDelete.id,
                first_name: subjectToDelete.code,
                last_name: `(${subjectToDelete.name})`,
                student_id_number: 'Module',
              }
            : null
        }
        isDeleting={isDeleting}
      />
    </div>
  );
}
