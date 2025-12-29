import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getRaceDetail, predictRace } from '../api';
import { ArrowLeft, Play, TrendingUp } from 'lucide-react';

const RaceDetail = () => {
        const { id } = useParams();
        const [race, setRace] = useState(null);
        const [horses, setHorses] = useState([]);
        const [loading, setLoading] = useState(true);
        const [predictions, setPredictions] = useState({}); // Map horse_id -> score
        const [predicting, setPredicting] = useState(false);

        useEffect(() => {
                const fetchData = async () => {
                        try {
                                const data = await getRaceDetail(id);
                                setRace(data.info);
                                setHorses(data.horses);
                        } catch (error) {
                                console.error("Failed to fetch race details", error);
                        } finally {
                                setLoading(false);
                        }
                };
                fetchData();
        }, [id]);

        const handlePredict = async () => {
                setPredicting(true);
                try {
                        const result = await predictRace(id);
                        // Map result array to object for easy lookup
                        const predMap = {};
                        result.predictions.forEach(p => {
                                predMap[p.horse_id] = p.score;
                        });
                        setPredictions(predMap);
                } catch (error) {
                        console.error("Prediction failed", error);
                        alert("Prediction failed. Check console.");
                } finally {
                        setPredicting(false);
                }
        };

        if (loading) return <div className="loading-screen">Loading Race Details...</div>;
        if (!race) return <div className="loading-screen">Race Not Found</div>;

        // Sort horses: if predictions exist, sort by score (asc/desc depending on meaning). 
        // Assuming Lower Score = Better Rank? Or Higher Score = Better Probability?
        // Model uses LightGBM Regression on Rank? If we regressed on Rank, Lower is Better.
        // Code in app.py: "df_out = df_out.sort_values('predicted_score')"
        // So standard sort order. Lower first.

        const sortedHorses = [...horses].sort((a, b) => {
                const scoreA = predictions[a.horse_id];
                const scoreB = predictions[b.horse_id];
                if (scoreA !== undefined && scoreB !== undefined) {
                        return scoreA - scoreB;
                }
                return 0; // Keep original order if not predicted
        });

        return (
                <div className="container">
                        <Link to="/" className="btn btn-ghost" style={{ marginTop: '20px', paddingLeft: 0 }}>
                                <ArrowLeft size={16} /> Back to Races
                        </Link>

                        <div className="card" style={{ marginTop: '20px' }}>
                                <div className="card-header">
                                        <div>
                                                <h1 className="card-title" style={{ fontSize: '1.5rem' }}>Race {race.race_id}</h1>
                                                <p className="card-subtitle">{race.course} | {race.weather} | {race.condition}</p>
                                        </div>
                                        <button
                                                className="btn btn-primary"
                                                onClick={handlePredict}
                                                disabled={predicting}
                                        >
                                                {predicting ? 'Analyzing...' : <> <Play size={16} /> Run Prediction </>}
                                        </button>
                                </div>

                                <table className="data-table">
                                        <thead>
                                                <tr>
                                                        <th>Waku</th>
                                                        <th>Horse</th>
                                                        <th>Jockey</th>
                                                        <th>Info</th>
                                                        <th>Actual Rank</th>
                                                        <th>Prediction</th>
                                                </tr>
                                        </thead>
                                        <tbody>
                                                {sortedHorses.map((horse) => {
                                                        const score = predictions[horse.horse_id];
                                                        const isPredicted = score !== undefined;

                                                        return (
                                                                <tr key={horse.horse_id} style={isPredicted ? { backgroundColor: 'rgba(59, 130, 246, 0.1)' } : {}}>
                                                                        <td>{horse.wakuban}</td>
                                                                        <td style={{ fontWeight: 500 }}>{horse.horse_id}</td>
                                                                        <td>{horse.jockey_id}</td>
                                                                        <td className="card-subtitle">{horse.sex}{horse.age} / {horse.weight}kg</td>
                                                                        <td>
                                                                                {horse.rank ? (
                                                                                        <span className={`rank-badge rank-${horse.rank}`}>{horse.rank}</span>
                                                                                ) : '-'}
                                                                        </td>
                                                                        <td>
                                                                                {isPredicted ? (
                                                                                        <div className="flex items-center gap-2 prediction-score">
                                                                                                <TrendingUp size={14} />
                                                                                                {score.toFixed(4)}
                                                                                        </div>
                                                                                ) : '-'}
                                                                        </td>
                                                                </tr>
                                                        );
                                                })}
                                        </tbody>
                                </table>
                        </div>
                </div>
        );
};

export default RaceDetail;
