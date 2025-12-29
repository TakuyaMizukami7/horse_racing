import React, { useState } from 'react';
import axios from 'axios';
import { Play, Plus, Trash2, ArrowRight } from 'lucide-react';

const RaceInput = () => {
        // Race Info State
        const [raceInfo, setRaceInfo] = useState({
                course_type: 'Grass',
                distance: 1600,
                weather: 'Sunny',
                condition: 'Good',
                place: 'Tokyo'
        });

        // Horses State
        const [horses, setHorses] = useState([
                { id: 1, wakuban: 1, name: '', jockey: '', age: 3, sex: 'Male', weight: 56.0 },
                { id: 2, wakuban: 2, name: '', jockey: '', age: 3, sex: 'Male', weight: 56.0 },
        ]);

        const [loading, setLoading] = useState(false);
        const [predictions, setPredictions] = useState(null);

        // New State for URL Scraping
        const [url, setUrl] = useState('');
        const [scraping, setScraping] = useState(false);

        const addHorse = () => {
                const newId = horses.length > 0 ? Math.max(...horses.map(h => h.id)) + 1 : 1;
                const nextWaku = horses.length > 0 ? (horses[horses.length - 1].wakuban % 8) + 1 : 1;
                setHorses([...horses, {
                        id: newId,
                        wakuban: nextWaku,
                        name: `Horse ${newId}`,
                        jockey: '',
                        age: 3,
                        sex: 'Male',
                        weight: 56.0
                }]);
        };

        const removeHorse = (id) => {
                setHorses(horses.filter(h => h.id !== id));
        };

        const updateHorse = (id, field, value) => {
                setHorses(horses.map(h => h.id === id ? { ...h, [field]: value } : h));
        };

        const handleScrape = async () => {
                if (!url) return;
                setScraping(true);
                try {
                        const response = await axios.post('/api/scrape_race', { url });
                        const data = response.data;

                        if (data) {
                                // Update Race Info
                                setRaceInfo({
                                        ...raceInfo,
                                        ...data.race_info
                                });

                                // Update Horses
                                const newHorses = data.horses.map((h, index) => ({
                                        id: index + 1,
                                        wakuban: h.wakuban,
                                        name: h.horse_id,
                                        jockey: h.jockey_id,
                                        age: h.age,
                                        sex: h.sex,
                                        weight: h.weight
                                }));
                                setHorses(newHorses);
                        }
                } catch (error) {
                        console.error("Scraping failed:", error);
                        alert("Failed to load race data. Check the URL.");
                } finally {
                        setScraping(false);
                }
        };

        const handlePredict = async () => {
                setLoading(true);
                setPredictions(null);
                try {
                        // Prepare payload
                        const payload = {
                                race_info: raceInfo,
                                horses: horses.map(h => ({
                                        horse_id: h.name, // Using Name as ID
                                        jockey_id: h.jockey,
                                        wakuban: parseInt(h.wakuban),
                                        age: parseInt(h.age),
                                        sex: h.sex,
                                        weight: parseFloat(h.weight)
                                }))
                        };

                        const response = await axios.post('/api/predict_custom', payload);
                        setPredictions(response.data.predictions);
                } catch (error) {
                        console.error("Prediction failed:", error);
                        alert("Prediction failed. Please check the backend.");
                } finally {
                        setLoading(false);
                }
        };

        return (
                <div className="container" style={{ paddingBottom: '50px' }}>
                        <div style={{ marginTop: '40px', marginBottom: '20px' }}>
                                <h1 className="header-title" style={{ fontSize: '2rem', fontWeight: 'bold' }}>Predict New Race</h1>
                                <p className="card-subtitle">Enter race details and participating horses.</p>
                        </div>

                        {/* Usage Instructions */}
                        <div className="card" style={{ marginBottom: '24px', backgroundColor: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)' }}>
                                <div className="card-header">
                                        <h2 className="card-title">How to Use</h2>
                                </div>
                                <div style={{ padding: '0 20px 20px 20px', lineHeight: '1.6' }}>
                                        <ol style={{ paddingLeft: '20px', margin: 0 }}>
                                                <li><strong>Paste Netkeiba URL</strong>: Copy the URL of a race card (Shutuba) from netkeiba.com (e.g., specific race page).</li>
                                                <li><strong>Fetch Data</strong>: Click the "Fetch Data" button to automatically fill in race conditions and horse details.</li>
                                                <li><strong>Review & Edit</strong>: Check the populated information. You can manually adjust conditions or add/remove horses if needed.</li>
                                                <li><strong>Run Prediction</strong>: Click "Run Prediction" at the bottom to see the AI's predicted ranking and winning probabilities.</li>
                                        </ol>
                                </div>
                        </div>

                        <div className="card" style={{ marginBottom: '24px', borderLeft: '4px solid var(--accent-gold)' }}>
                                <div className="card-header">
                                        <h2 className="card-title">Auto-Fill from URL</h2>
                                </div>
                                <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
                                        <input
                                                type="text"
                                                className="input-field"
                                                placeholder="Paste Netkeiba Shutuba URL (e.g., https://race.netkeiba.com/...)"
                                                value={url}
                                                onChange={(e) => setUrl(e.target.value)}
                                                style={{ flex: 1 }}
                                        />
                                        <button
                                                className="btn btn-secondary"
                                                onClick={handleScrape}
                                                disabled={scraping}
                                                style={{ minWidth: '120px' }}
                                        >
                                                {scraping ? 'Loading...' : 'Fetch Data'}
                                        </button>
                                </div>
                        </div>

                        <div className="card">
                                <div className="card-header">
                                        <h2 className="card-title">Race Conditions</h2>
                                </div>
                                <div className="race-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginTop: '10px', gap: '16px' }}>
                                        <div>
                                                <label className="input-label">Track Type</label>
                                                <select
                                                        className="input-field"
                                                        value={raceInfo.course_type}
                                                        onChange={(e) => setRaceInfo({ ...raceInfo, course_type: e.target.value })}
                                                >
                                                        <option value="Grass">Grass (芝)</option>
                                                        <option value="Dirt">Dirt (ダート)</option>
                                                </select>
                                        </div>

                                        <div>
                                                <label className="input-label">Distance (m)</label>
                                                <input
                                                        type="number"
                                                        className="input-field"
                                                        value={raceInfo.distance}
                                                        onChange={(e) => setRaceInfo({ ...raceInfo, distance: parseInt(e.target.value) })}
                                                />
                                        </div>

                                        <div>
                                                <label className="input-label">Weather</label>
                                                <select
                                                        className="input-field"
                                                        value={raceInfo.weather}
                                                        onChange={(e) => setRaceInfo({ ...raceInfo, weather: e.target.value })}
                                                >
                                                        <option value="Sunny">Sunny (晴)</option>
                                                        <option value="Cloudy">Cloudy (曇)</option>
                                                        <option value="Rainy">Rainy (雨)</option>
                                                </select>
                                        </div>

                                        <div>
                                                <label className="input-label">Condition</label>
                                                <select
                                                        className="input-field"
                                                        value={raceInfo.condition}
                                                        onChange={(e) => setRaceInfo({ ...raceInfo, condition: e.target.value })}
                                                >
                                                        <option value="Good">Good (良)</option>
                                                        <option value="Yielding">Yielding (稍重)</option>
                                                        <option value="Soft">Soft (重)</option>
                                                        <option value="Heavy">Heavy (不良)</option>
                                                </select>
                                        </div>
                                </div>
                        </div>

                        <div className="card" style={{ marginTop: '24px' }}>
                                <div className="card-header">
                                        <h2 className="card-title">Participating Horses</h2>
                                        <button className="btn btn-ghost" onClick={addHorse}>
                                                <Plus size={16} /> Add Horse
                                        </button>
                                </div>

                                <table className="data-table input-table">
                                        <thead>
                                                <tr>
                                                        <th style={{ width: '60px' }}>Waku</th>
                                                        <th>Horse Name</th>
                                                        <th>Jockey</th>
                                                        <th style={{ width: '80px' }}>Sex</th>
                                                        <th style={{ width: '80px' }}>Age</th>
                                                        <th style={{ width: '100px' }}>Weight</th>
                                                        <th style={{ width: '60px' }}></th>
                                                </tr>
                                        </thead>
                                        <tbody>
                                                {horses.map((horse) => (
                                                        <tr key={horse.id}>
                                                                <td>
                                                                        <input type="number" className="input-mini" value={horse.wakuban}
                                                                                onChange={(e) => updateHorse(horse.id, 'wakuban', e.target.value)} />
                                                                </td>
                                                                <td>
                                                                        <input type="text" className="input-field" value={horse.name} placeholder="Name"
                                                                                onChange={(e) => updateHorse(horse.id, 'name', e.target.value)} />
                                                                </td>
                                                                <td>
                                                                        <input type="text" className="input-field" value={horse.jockey} placeholder="Jockey"
                                                                                onChange={(e) => updateHorse(horse.id, 'jockey', e.target.value)} />
                                                                </td>
                                                                <td>
                                                                        <select className="input-field" value={horse.sex}
                                                                                onChange={(e) => updateHorse(horse.id, 'sex', e.target.value)}>
                                                                                <option value="Male">Male</option>
                                                                                <option value="Female">Female</option>
                                                                                <option value="Gelding">Gelding</option>
                                                                        </select>
                                                                </td>
                                                                <td>
                                                                        <input type="number" className="input-mini" value={horse.age}
                                                                                onChange={(e) => updateHorse(horse.id, 'age', e.target.value)} />
                                                                </td>
                                                                <td>
                                                                        <input type="number" className="input-mini" value={horse.weight} step="0.5"
                                                                                onChange={(e) => updateHorse(horse.id, 'weight', e.target.value)} />
                                                                </td>
                                                                <td>
                                                                        {horses.length > 2 && (
                                                                                <button className="btn-icon-danger" onClick={() => removeHorse(horse.id)}>
                                                                                        <Trash2 size={16} />
                                                                                </button>
                                                                        )}
                                                                </td>
                                                        </tr>
                                                ))}
                                        </tbody>
                                </table>
                        </div>

                        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
                                <button
                                        className="btn btn-primary"
                                        onClick={handlePredict}
                                        disabled={loading}
                                        style={{ fontSize: '1.2rem', padding: '12px 32px' }}
                                >
                                        {loading ? 'Analyzing...' : <>Run Prediction <ArrowRight size={20} /></>}
                                </button>
                        </div>

                        {predictions && (
                                <div className="card" style={{ marginTop: '40px', borderColor: 'var(--accent-gold)' }}>
                                        <div className="card-header">
                                                <h2 className="card-title text-gold">Prediction Results</h2>
                                        </div>
                                        <table className="data-table">
                                                <thead>
                                                        <tr>
                                                                <th>Rank</th>
                                                                <th>#</th>
                                                                <th>Horse</th>
                                                                <th>Jockey</th>
                                                                <th>Confidence</th>
                                                        </tr>
                                                </thead>
                                                <tbody>
                                                        {predictions.map((p, idx) => (
                                                                <tr key={idx} className={idx < 3 ? `row-rank-${idx + 1}` : ''}>
                                                                        <td>
                                                                                <span className={idx < 3 ? `rank-badge rank-${idx + 1}` : ''}>
                                                                                        {idx + 1}
                                                                                </span>
                                                                        </td>
                                                                        <td>{p.wakuban}</td>
                                                                        <td style={{ fontWeight: 'bold' }}>{p.horse_id}</td>
                                                                        <td>{p.jockey_id}</td>
                                                                        <td className="prediction-score" style={{ color: p.confidence > 20 ? 'var(--accent-gold)' : 'inherit' }}>
                                                                                {p.confidence.toFixed(1)}%
                                                                        </td>
                                                                </tr>
                                                        ))}
                                                </tbody>
                                        </table>
                                </div>
                        )}
                </div>
        );
};

export default RaceInput;
