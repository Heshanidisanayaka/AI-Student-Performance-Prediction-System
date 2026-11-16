import api from './api';

export const studentService = {
  async getStudents(params = {}) {
    const cleanParams = {};
    Object.keys(params).forEach((key) => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        cleanParams[key] = params[key];
      }
    });

    const response = await api.get('/students/', { params: cleanParams });
    return response.data;
  },

  async getStudentById(id) {
    const response = await api.get(`/students/${id}`);
    return response.data;
  },

  async createStudent(studentData) {
    const response = await api.post('/students/', studentData);
    return response.data;
  },

  async updateStudent(id, studentData) {
    const response = await api.put(`/students/${id}`, studentData);
    return response.data;
  },

  async deleteStudent(id) {
    const response = await api.delete(`/students/${id}`);
    return response.data;
  },
};
