import axios from 'axios';

const api = axios.create({
        baseURL: '/api', // Relative URL for deployment
});

export const getRaces = async () => {
        const response = await api.get('/races');
        return response.data;
};

export const getRaceDetail = async (raceId) => {
        const response = await api.get(`/races/${raceId}`);
        return response.data;
};

export const predictRace = async (raceId) => {
        const response = await api.post(`/predict/${raceId}`);
        return response.data;
};
