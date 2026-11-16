import React, { useState, useEffect } from 'react';
import { X, AlertCircle } from 'lucide-react';

export default function StudentModal({ isOpen, onClose, onSubmit, initialData = null, isSubmitting = false, error = null }) {
  const isEditing = Boolean(initialData);

  const [formData, setFormData] = useState({
    student_id_number: '',
    first_name: '',
    last_name: '',
    email: '',
    department: 'Computer Science',
    academic_year: '2025-2026',
    class_name: 'CS-3A',
    current_semester: 1,
    enrollment_year: 2026,
    gender: 'Other',
    status: 'active',
  });

  const [clientErrors, setClientErrors] = useState({});

  useEffect(() => {
    if (initialData) {
      setFormData({
        student_id_number: initialData.student_id_number || '',
        first_name: initialData.first_name || '',
        last_name: initialData.last_name || '',
        email: initialData.email || '',
        department: initialData.department || 'Computer Science',
        academic_year: initialData.academic_year || '2025-2026',
        class_name: initialData.class_name || 'CS-3A',
        current_semester: initialData.current_semester || 1,
        enrollment_year: initialData.enrollment_year || 2026,
        gender: initialData.gender || 'Other',
        status: initialData.status || 'active',
      });
    } else {
      setFormData({
        student_id_number: '',
        first_name: '',
        last_name: '',
        email: '',
        department: 'Computer Science',
        academic_year: '2025-2026',
        class_name: 'CS-3A',
        current_semester: 1,
        enrollment_year: 2026,
        gender: 'Other',
        status: 'active',
      });
    }
    setClientErrors({});
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'current_semester' || name === 'enrollment_year' ? Number(value) : value,
    }));
    if (clientErrors[name]) {
      setClientErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const errs = {};
    if (!formData.student_id_number.trim()) errs.student_id_number = 'Student ID is required.';
    if (!formData.first_name.trim()) errs.first_name = 'First name is required.';
    if (!formData.last_name.trim()) errs.last_name = 'Last name is required.';
    if (!formData.email.trim()) {
      errs.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      errs.email = 'Please enter a valid email address.';
    }
    if (!formData.department.trim()) errs.department = 'Department is required.';
    if (!formData.class_name.trim()) errs.class_name = 'Class is required.';
    return errs;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setClientErrors(errs);
      return;
    }
    onSubmit(formData);
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog">
        <div className="modal-header">
          <h3>{isEditing ? 'Edit Student Profile' : 'Add New Student'}</h3>
          <button type="button" className="icon-btn" onClick={onClose} disabled={isSubmitting}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="modal-alert-error">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-grid">
            <div className="form-group">
              <label>Student ID Number *</label>
              <input
                type="text"
                name="student_id_number"
                value={formData.student_id_number}
                onChange={handleChange}
                placeholder="e.g. STU2026001"
                required
              />
              {clientErrors.student_id_number && (
                <span className="field-error">{clientErrors.student_id_number}</span>
              )}
            </div>

            <div className="form-group">
              <label>Institutional Email *</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="student@university.edu"
                required
              />
              {clientErrors.email && <span className="field-error">{clientErrors.email}</span>}
            </div>

            <div className="form-group">
              <label>First Name *</label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                placeholder="e.g. John"
                required
              />
              {clientErrors.first_name && <span className="field-error">{clientErrors.first_name}</span>}
            </div>

            <div className="form-group">
              <label>Last Name *</label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                placeholder="e.g. Doe"
                required
              />
              {clientErrors.last_name && <span className="field-error">{clientErrors.last_name}</span>}
            </div>

            <div className="form-group">
              <label>Department / Major *</label>
              <select name="department" value={formData.department} onChange={handleChange}>
                <option value="Computer Science">Computer Science</option>
                <option value="Information Technology">Information Technology</option>
                <option value="Data Science">Data Science</option>
                <option value="Software Engineering">Software Engineering</option>
                <option value="Cybernetics">Cybernetics</option>
                <option value="Electrical Engineering">Electrical Engineering</option>
              </select>
            </div>

            <div className="form-group">
              <label>Class / Section *</label>
              <input
                type="text"
                name="class_name"
                value={formData.class_name}
                onChange={handleChange}
                placeholder="e.g. CS-3A"
                required
              />
              {clientErrors.class_name && <span className="field-error">{clientErrors.class_name}</span>}
            </div>

            <div className="form-group">
              <label>Academic Year</label>
              <select name="academic_year" value={formData.academic_year} onChange={handleChange}>
                <option value="2025-2026">2025-2026</option>
                <option value="2024-2025">2024-2025</option>
                <option value="2026-2027">2026-2027</option>
              </select>
            </div>

            <div className="form-group">
              <label>Current Semester</label>
              <select name="current_semester" value={formData.current_semester} onChange={handleChange}>
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Gender</label>
              <select name="gender" value={formData.gender} onChange={handleChange}>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label>Academic Status</label>
              <select name="status" value={formData.status} onChange={handleChange}>
                <option value="active">Active (Good Standing)</option>
                <option value="at_risk">At Risk (Needs Intervention)</option>
                <option value="graduated">Graduated</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? (isEditing ? 'Saving Changes...' : 'Creating Student...') : (isEditing ? 'Save Changes' : 'Create Student')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
