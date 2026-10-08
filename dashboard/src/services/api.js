import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
});

export const getOverview = () => api.get('/overview').then(res => res.data);
export const getCategories = () => api.get('/categories').then(res => res.data);
export const getUploadTimes = () => api.get('/upload-times').then(res => res.data);
export const getTitleAnalysis = () => api.get('/title-analysis').then(res => res.data);
export const getTrendingFactors = () => api.get('/trending-factors').then(res => res.data);
export const getBreakoutVideos = () => api.get('/breakout-videos').then(res => res.data);
export const getPipelineStatus = () => api.get('/pipeline-status').then(res => res.data);
export const getDataQuality = () => api.get('/data-quality').then(res => res.data);
export const getVideos = (params) => api.get('/videos', { params }).then(res => res.data);
export const getTrendScore = (videoId) => api.get(`/trend-score/${videoId}`).then(res => res.data);

export default api;
