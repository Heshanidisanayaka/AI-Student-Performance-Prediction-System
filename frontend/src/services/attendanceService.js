import api from './api';

export const attendanceService = {
  /**
   * Query attendance history with optional filters (subject, student, dates, status, session, page, size)
   */
  async getAttendanceRecords(params = {}) {
    const cleanParams = {};
    Object.keys(params).forEach((key) => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        cleanParams[key] = params[key];
      }
    });

    const response = await api.get('/attendance/', { params: cleanParams });
    return response.data;
  },

  /**
   * Bulk-record attendance for an entire classroom session
   */
  async recordSessionAttendance(sessionData) {
    const response = await api.post('/attendance/session', sessionData);
    return response.data;
  },

  /**
   * Record attendance for a single student
   */
  async recordSingleAttendance(data) {
    const response = await api.post('/attendance/', data);
    return response.data;
  },

  /**
   * Update attendance status or excuse remarks
   */
  async updateAttendance(id, updateData) {
    const response = await api.put(`/attendance/${id}`, updateData);
    return response.data;
  },

  /**
   * Delete an erroneous attendance record
   */
  async deleteAttendance(id) {
    const response = await api.delete(`/attendance/${id}`);
    return response.data;
  },

  /**
   * Get student attendance statistics with institutional excused absence calculation
   */
  async getStudentStats(studentId) {
    const response = await api.get(`/attendance/stats/student/${studentId}`);
    return response.data;
  },

  /**
   * Fetch aggregated analytics for Recharts visualizations
   */
  async getAttendanceAnalytics(subjectId = null) {
    const params = subjectId ? { subject_id: subjectId } : {};
    const response = await api.get('/attendance/analytics', { params });
    return response.data;
  },
};

export default attendanceService;
