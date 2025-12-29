import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getRaces } from '../api';
import { Calendar, MapPin, Trophy } from 'lucide-react';

const RaceList = () => {
        const [races, setRaces] = useState([]);
        const [loading, setLoading] = useState(true);

        useEffect(() => {
                const fetchRaces = async () => {
                        try {
                                const data = await getRaces();
                                setRaces(data);
                        } catch (error) {
                                console.error("Failed to fetch races", error);
                        } finally {
                                setLoading(false);
                        }
                };
                fetchRaces();
        }, []);

        if (loading) return <div className="loading-screen">Loading Races...</div>;

        return (
                <div className="container">
                        <div style={{ marginTop: '40px', marginBottom: '20px' }}>
                                <h1 className="header-title" style={{ fontSize: '2rem', fontWeight: 'bold' }}>Available Races</h1>
                                <p className="card-subtitle">Select a race to view details and predictions.</p>
                        </div>

                        <div className="race-grid">
                                {races.map((race) => (
                                        <Link to={`/races/${race.race_id}`} key={race.race_id} className="card">
                                                <div className="card-header">
                                                        <span className="card-title">Race {race.race_id?.slice(-2)}</span>
                                                        <span className="card-subtitle text-gold"><Trophy size={16} /></span>
                                                </div>

                                                <div className="flex items-center gap-2 mb-4" style={{ color: 'var(--text-secondary)' }}>
                                                        <MapPin size={16} />
                                                        <span>{race.course}</span>
                                                </div>

                                                <div className="flex items-center gap-2" style={{ color: 'var(--text-secondary)' }}>
                                                        <Calendar size={16} />
                                                        <span>{race.weather} / {race.condition}</span>
                                                </div>

                                                <div style={{ marginTop: '16px', fontSize: '0.875rem' }}>
                                                        {race.horses_count} Horses Entered
                                                </div>
                                        </Link>
                                ))}
                        </div>
                </div>
        );
};

export default RaceList;
