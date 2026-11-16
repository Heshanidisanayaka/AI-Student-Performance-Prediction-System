import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

export default function DeleteConfirmModal({ isOpen, onClose, onConfirm, student, isDeleting }) {
  if (!isOpen || !student) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog modal-small">
        <div className="modal-header">
          <h3 className="danger-text">Delete Student</h3>
          <button type="button" className="icon-btn" onClick={onClose} disabled={isDeleting}>
            <X size={20} />
          </button>
        </div>

        <div className="delete-modal-content">
          <div className="warning-icon-wrapper">
            <AlertTriangle size={36} color="#ef4444" />
          </div>
          <p>
            Are you sure you want to permanently delete student{' '}
            <strong>
              {student.first_name} {student.last_name} ({student.student_id_number})
            </strong>
            ?
          </p>
          <span className="warning-subtext">
            This action cannot be undone. Associated attendance, academic records, and prediction logs will be deleted.
          </span>
        </div>

        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose} disabled={isDeleting}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-danger"
            onClick={() => onConfirm(student.id)}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Permanently Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}
