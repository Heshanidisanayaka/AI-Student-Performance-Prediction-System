import api from './api';

export const subjectService = {
  async getSubjects(params = {}) {
    const cleanParams = {};
    Object.keys(params).forEach((key) => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        cleanParams[key] = params[key];
      }
    });

    const response = await api.get('/subjects/', { params: cleanParams });
    return response.data;
  },

  async getSubjectById(id) {
    const response = await api.get(`/subjects/${id}`);
    return response.data;
  },

  async createSubject(subjectData) {
    const response = await api.post('/subjects/', subjectData);
    return response.data;
  },

  async updateSubject(id, subjectData) {
    const response = await api.put(`/subjects/${id}`, subjectData);
    return response.data;
  },

  async toggleDeactivate(id, isActive) {
    const response = await api.patch(`/subjects/${id}/deactivate`, null, {
      params: { is_active: isActive },
    });
    return response.data;
  },

  async deleteSubject(id) {
    const response = await api.delete(`/subjects/${id}`);
    return response.data;
  },

  async assignLecturer(subjectId, lecturerId) {
    const response = await api.post(`/subjects/${subjectId}/lecturer`, {
      lecturer_id: lecturerId,
    });
    return response.data;
  },

  async getEnrolledStudents(subjectId) {
    const response = await api.get(`/subjects/${subjectId}/students`);
    return response.data;
  },

  async enrollStudents(subjectId, studentIds, academicYear = '2025-2026') {
    const response = await api.post(`/subjects/${subjectId}/enroll`, {
      student_ids: studentIds,
      academic_year: academicYear,
    });
    return response.data;
  },

  async unenrollStudent(subjectId, studentId) {
    const response = await api.delete(`/subjects/${subjectId}/enroll/${studentId}`);
    return response.data;
  },
};
