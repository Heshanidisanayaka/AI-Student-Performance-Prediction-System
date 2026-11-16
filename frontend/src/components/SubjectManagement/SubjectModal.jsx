import React, { useState, useEffect } from 'react';
import { X, AlertCircle } from 'lucide-react';

export default function SubjectModal({ isOpen, onClose, onSubmit, initialData = null, isSubmitting = false, error = null }) {
  const isEditing = Boolean(initialData);

  const [formData, setFormData] = useState({
    code: '',
    name: '',
    description: '',
    credits: 3,
    department: 'Computer Science',
    semester: 1,
    academic_year: '2025-2026',
    is_active: true,
  });

  const [clientErrors, setClientErrors] = useState({});

  useEffect(() => {
    if (initialData) {
      setFormData({
        code: initialData.code || '',
        name: initialData.name || '',
        description: initialData.description || '',
        credits: initialData.credits || 3,
        department: initialData.department || 'Computer Science',
        semester: initialData.semester || 1,
        academic_year: initialData.academic_year || '2025-2026',
        is_active: initialData.is_active !== undefined ? initialData.is_active : true,
      });
    } else {
      setFormData({
        code: '',
        name: '',
        description: '',
        credits: 3,
        department: 'Computer Science',
        semester: 1,
        academic_year: '2025-2026',
        is_active: true,
      });
    }
    setClientErrors({});
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (name === 'credits' || name === 'semester' ? Number(value) : value),
    }));
    if (clientErrors[name]) {
      setClientErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const errs = {};
    if (!formData.code.trim()) errs.code = 'Subject code is required (e.g. CS101).';
    if (!formData.name.trim()) errs.name = 'Subject title is required.';
    if (!formData.department.trim()) errs.department = 'Department is required.';
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
          <h3>{isEditing ? 'Edit Subject / Module' : 'Create New Subject'}</h3>
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
              <label>Subject Code *</label>
              <input
                type="text"
                name="code"
                value={formData.code}
                onChange={handleChange}
                placeholder="e.g. CS101, MATH201"
                required
              />
              {clientErrors.code && <span className="field-error">{clientErrors.code}</span>}
            </div>

            <div className="form-group">
              <label>Academic Year</label>
              <select name="academic_year" value={formData.academic_year} onChange={handleChange}>
                <option value="2025-2026">2025-2026</option>
                <option value="2024-2025">2024-2025</option>
                <option value="2026-2027">2026-2027</option>
              </select>
            </div>

            <div className="form-group full-width" style={{ gridColumn: 'span 2' }}>
              <label>Subject Title *</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="e.g. Data Structures & Algorithms"
                required
              />
              {clientErrors.name && <span className="field-error">{clientErrors.name}</span>}
            </div>

            <div className="form-group full-width" style={{ gridColumn: 'span 2' }}>
              <label>Description & Learning Objectives</label>
              <textarea
                name="description"
                rows="3"
                value={formData.description}
                onChange={handleChange}
                placeholder="Brief summary of syllabus and prerequisites..."
                style={{
                  padding: '0.65rem 0.85rem',
                  borderRadius: '6px',
                  border: '1px solid #cbd5e1',
                  fontFamily: 'inherit',
                  fontSize: '0.88rem',
                }}
              />
            </div>

            <div className="form-group">
              <label>Department *</label>
              <select name="department" value={formData.department} onChange={handleChange}>
                <option value="Computer Science">Computer Science</option>
                <option value="Information Technology">Information Technology</option>
                <option value="Data Science">Data Science</option>
                <option value="Software Engineering">Software Engineering</option>
                <option value="Mathematics">Mathematics</option>
                <option value="Cybernetics">Cybernetics</option>
              </select>
            </div>

            <div className="form-group">
              <label>Credit Units (ECTS/Credits)</label>
              <select name="credits" value={formData.credits} onChange={handleChange}>
                {[1, 2, 3, 4, 5, 6, 8].map((c) => (
                  <option key={c} value={c}>
                    {c} Credit{c > 1 ? 's' : ''}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Semester</label>
              <select name="semester" value={formData.semester} onChange={handleChange}>
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ justifyContent: 'center' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  style={{ width: '18px', height: '18px' }}
                />
                <span>Active Course Offering</span>
              </label>
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Subject'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
