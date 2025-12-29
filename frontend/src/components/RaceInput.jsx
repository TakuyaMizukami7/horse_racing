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
                                        <h2 className="card-title">使い方ガイド (User Guide)</h2>
                                </div>
                                <div style={{ padding: '0 20px 20px 20px', lineHeight: '1.6' }}>
                                        <h3 style={{ fontSize: '1.1rem', color: 'var(--accent-gold)', marginTop: '0' }}>1. 使い方</h3>
                                        <ol style={{ paddingLeft: '20px', margin: '0 0 16px 0' }}>
                                                <li><strong>URLの貼り付け</strong>: netkeiba.comの出馬表ページ（例: 特定のレースページ）のURLをコピーします。</li>
                                                <li><strong>データの取得</strong>: "Fetch Data"ボタンをクリックすると、コース条件や出走馬データが自動入力されます。</li>
                                                <li><strong>確認・編集</strong>: 自動入力された情報を確認します。必要に応じて条件の手修正や、馬の追加・削除が可能です。</li>
                                                <li><strong>予測実行</strong>: ページ下部の "Run Prediction" ボタンを押すと、AIによる予測順位と勝率が表示されます。</li>
                                        </ol>

                                        <h3 style={{ fontSize: '1.1rem', color: 'var(--accent-gold)' }}>2. 結果の見方</h3>
                                        <ul style={{ paddingLeft: '20px', margin: '0 0 16px 0' }}>
                                                <li><strong>Rank</strong>: AIが予測したゴール順位です。数字が小さいほど上位争いをする可能性が高いです。</li>
                                                <li><strong>Confidence</strong>: その馬が勝つ確率（自信度）を示します。数値が高いほどAIの推奨度が高まります。</li>
                                                <li><strong>ハイライト</strong>: 特に期待値が高い（Confidence 20%以上）馬は、スコアが金色で強調表示されます。</li>
                                        </ul>

                                        <h3 style={{ fontSize: '1.1rem', color: 'var(--accent-gold)' }}>3. おすすめの馬券の買い方</h3>
                                        <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '8px' }}>
                                                <p style={{ margin: '0 0 8px 0' }}><strong>🔰 初心者・堅実派向け</strong></p>
                                                <ul style={{ paddingLeft: '20px', margin: 0 }}>
                                                        <li><strong>単勝・複勝</strong>: Rank 1 の馬（Confidenceが最も高い馬）を狙うのが基本です。</li>
                                                        <li><strong>ワイド・馬連</strong>: Rank 1〜3 の3頭ボックス（計3通り）がバランスの良い買い方です。</li>
                                                </ul>
                                                <p style={{ margin: '12px 0 8px 0' }}><strong>🎯 中級者・高配当狙い</strong></p>
                                                <ul style={{ paddingLeft: '20px', margin: 0 }}>
                                                        <li><strong>三連複・三連単</strong>: Rank 1 の馬を軸（1頭目）にし、相手に Rank 2〜5 の馬へ流す（フォーメーション）と、点数を抑えつつ的中を狙えます。</li>
                                                </ul>
                                        </div>
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

                        )}

                        {predictions && (
                                <>
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

                                        {/* Dynamic Betting Advice */}
                                        <BettingAdvice predictions={predictions} />
                                </>
                        )}
                </div>
        );
};

// Helper Component for Betting Advice
const BettingAdvice = ({ predictions }) => {
        if (!predictions || predictions.length < 2) return null;

        const top1 = predictions[0];
        const top2 = predictions[1];
        const top3 = predictions[2];

        // Logic to determine pattern
        let pattern = "UNKNOWN";
        let title = "";
        let description = "";
        let recommendation = [];

        // Thresholds
        const STRONG_FAVORITE_THRESHOLD = 25.0;
        const TWO_HORSE_THRESHOLD = 15.0;

        if (top1.confidence >= STRONG_FAVORITE_THRESHOLD) {
                pattern = "HONMEI";
                title = "🦁 本命堅実パターン (Solid Favorite)";
                description = `1位の ${top1.horse_id} が${top1.confidence.toFixed(1)}%と高い信頼度を示しています。この馬を軸にするのが定石です。`;
                recommendation = [
                        `単勝: ${top1.horse_id} (自信度大)`,
                        `馬単/馬連: ${top1.horse_id} → ${top2.horse_id}, ${top3?.horse_id}`
                ];
        } else if (top1.confidence >= TWO_HORSE_THRESHOLD && top2.confidence >= TWO_HORSE_THRESHOLD && (top1.confidence - top2.confidence) < 5.0) {
                pattern = "TAIKOU";
                title = "⚔️ 2強対決パターン (Two-Horse Race)";
                description = `1位 ${top1.horse_id} と 2位 ${top2.horse_id} が拮抗しており、3位以下を引き離しています。`;
                recommendation = [
                        `ワイド/馬連: ${top1.horse_id} - ${top2.horse_id} の1点`,
                        `3連複: ${top1.horse_id}, ${top2.horse_id} の2頭軸`
                ];
        } else {
                pattern = "KONSEN";
                title = "🌪️ 混戦パターン (Chaotic)";
                description = "突出した馬がおらず、混戦模様です。人気薄の馬にもチャンスがあります。";
                recommendation = [
                        `ワイドBOX: 上位3〜4頭 (${top1.horse_id}, ${top2.horse_id}, ${top3?.horse_id}...)`,
                        `3連複: フォーメーションで手広く`
                ];
        }

        return (
                <div className="card" style={{ marginTop: '24px', background: 'linear-gradient(145deg, rgba(255, 215, 0, 0.1), rgba(0, 0, 0, 0.4))', border: '1px solid var(--accent-gold)' }}>
                        <div className="card-header">
                                <h2 className="card-title" style={{ color: 'var(--accent-gold)' }}>AI Betting Strategy</h2>
                        </div>
                        <div style={{ padding: '0 20px 20px' }}>
                                <h3 style={{ marginTop: 0, fontSize: '1.2rem' }}>{title}</h3>
                                <p style={{ marginBottom: '16px' }}>{description}</p>
                                <div style={{ backgroundColor: 'rgba(0, 0, 0, 0.3)', padding: '12px', borderRadius: '8px' }}>
                                        <strong>🎯 おすすめの買い目:</strong>
                                        <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                                                {recommendation.map((rec, i) => (
                                                        <li key={i} style={{ marginBottom: '4px' }}>{rec}</li>
                                                ))}
                                        </ul>
                                </div>
                        </div>
                </div>
        );
};

export default RaceInput;
