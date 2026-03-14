import React, { useEffect, useState, useMemo } from 'react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar
} from 'recharts';
import api, { getProfile, getUserSubmissions } from '../api';
import { Award, Target, Activity, Zap } from 'lucide-react';

function Dashboard({ user }) {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [activeSkillLang, setActiveSkillLang] = useState('python');

  useEffect(() => {
    async function loadData() {
      if (!user?.id) return;
      try {
        setLoading(true);
        const [profData, subData] = await Promise.all([
          getProfile(user.id),
          getUserSubmissions(user.id)
        ]);
        setProfile(profData);
        setSubmissions(subData);
      } catch (err) {
        console.error("Dashboard failed to load", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [user]);

  // Aggregate stats
  const stats = useMemo(() => {
    const totalSubmissions = submissions.length;
    const errorCount = submissions.filter(s => s.result !== "ok" && s.result !== "analysis_completed").length;
    let rank = "Novice";
    if (totalSubmissions > 50) rank = "Master";
    else if (totalSubmissions > 20) rank = "Advanced";
    else if (totalSubmissions > 5) rank = "Intermediate";
    
    return {
      totalSubmissions,
      errorRate: totalSubmissions ? Math.round((errorCount / totalSubmissions) * 100) : 0,
      rank,
      languages: [...new Set(submissions.map(s => s.language))]
    };
  }, [submissions]);

  // History for standard chart
  const historyData = useMemo(() => {
    if (!profile?.profiles) return [];
    // Convert backend profiles into chartable objects
    return profile.profiles.map(p => ({
      name: `Sub ${p.submissions_count}`,
      confidence: Math.round(p.confidence_score * 100),
      mastery: Math.min(100, Math.round(p.confidence_score * 120)) // proxy for visual
    }));
  }, [profile]);

  // Skill graph data filtered by lang
  const availableSkillLangs = useMemo(() => {
    if (!profile?.skill_scores) return [];
    return [...new Set(profile.skill_scores.map(s => s.language || 'python'))];
  }, [profile]);

  useEffect(() => {
    if (availableSkillLangs.length > 0 && !availableSkillLangs.includes(activeSkillLang)) {
      setActiveSkillLang(availableSkillLangs[0]);
    }
  }, [availableSkillLangs, activeSkillLang]);

  const radarData = useMemo(() => {
    if (!profile?.skill_scores) return [];
    return profile.skill_scores
      .filter(s => (s.language || 'python') === activeSkillLang)
      .map(s => ({
        ...s,
        concept: s.concept.replace(/_/g, " "),
      }));
  }, [profile, activeSkillLang]);

  if (loading) return <div className="p-10 flex justify-center"><div className="spinner w-8 h-8" /></div>;

  return (
    <div className="flex flex-col h-full overflow-y-auto w-full p-8 bg-[var(--bg-primary)]">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
            Learning Analytics Dashboard
          </h1>
          <p className="text-gray-400 mt-2">Track your coding mastery, confidence trajectories, and concept skills.</p>
        </div>
        <div className="flex gap-4">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] px-4 py-2 rounded-lg flex items-center gap-3">
            <Award className="text-yellow-500" />
            <div>
              <p className="text-xs text-[var(--text-secondary)] font-semibold uppercase">Current Rank</p>
              <p className="font-bold text-[var(--text-primary)]">{stats.rank}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Top Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card p-6 flex items-center gap-4 border-l-4 border-l-blue-500">
          <div className="p-3 bg-blue-500/10 rounded-lg"><Activity className="text-blue-500" size={24}/></div>
          <div>
            <p className="text-sm text-gray-400 font-semibold mb-1">Total Submissions</p>
            <p className="text-2xl font-bold">{stats.totalSubmissions}</p>
          </div>
        </div>

        <div className="card p-6 flex items-center gap-4 border-l-4 border-l-indigo-500">
          <div className="p-3 bg-indigo-500/10 rounded-lg"><Target className="text-indigo-500" size={24}/></div>
          <div>
            <p className="text-sm text-gray-400 font-semibold mb-1">Average Confidence</p>
            <p className="text-2xl font-bold">
              {historyData.length > 0 ? historyData[historyData.length - 1].confidence : 0}%
            </p>
          </div>
        </div>

        <div className="card p-6 flex items-center gap-4 border-l-4 border-l-red-500">
          <div className="p-3 bg-red-500/10 rounded-lg"><Zap className="text-red-500" size={24}/></div>
          <div>
            <p className="text-sm text-gray-400 font-semibold mb-1">Mistake Rate</p>
            <p className="text-2xl font-bold">{stats.errorRate}%</p>
          </div>
        </div>
        
        <div className="card p-6 flex items-center gap-4 border-l-4 border-l-emerald-500">
          <div className="p-3 bg-emerald-500/10 rounded-lg"><Award className="text-emerald-500" size={24}/></div>
          <div>
            <p className="text-sm text-gray-400 font-semibold mb-1">Languages Used</p>
            <div className="flex gap-2 mt-1 flex-wrap">
              {stats.languages.map(l => (
                <span key={l} className="text-xs bg-[var(--bg-secondary)] px-2 py-1 rounded text-[var(--text-primary)]">{l}</span>
              ))}
              {stats.languages.length === 0 && <span className="text-xs text-gray-500">None</span>}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Trajectory */}
        <div className="card p-6 lg:col-span-2 slide-up">
          <h3 className="text-lg font-bold mb-6 text-[var(--text-primary)]">Confidence Trajectory (Over Time)</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                <XAxis dataKey="name" stroke="#666" tick={{fill: '#888'}} />
                <YAxis stroke="#666" tick={{fill: '#888'}} domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#2a2a3c', borderColor: '#444', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="confidence" 
                  stroke="#3b82f6" 
                  strokeWidth={3}
                  activeDot={{ r: 8 }} 
                  name="Confidence %"
                />
                <Line 
                  type="monotone" 
                  dataKey="mastery" 
                  stroke="#10b981" 
                  strokeWidth={3}
                  name="Concept Mastery %"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Skill Radar */}
        <div className="card p-6 slide-up" style={{ animationDelay: '0.1s' }}>
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-[var(--text-primary)]">Current Concept Skills</h3>
            {availableSkillLangs.length > 0 && (
              <div className="flex gap-1">
                {availableSkillLangs.map(l => (
                  <button
                    key={l}
                    onClick={() => setActiveSkillLang(l)}
                    className={`px-2 py-1 text-[0.7rem] uppercase font-bold rounded ${
                      activeSkillLang === l 
                        ? 'bg-[var(--accent)] text-white' 
                        : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    {l}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          {radarData.length > 0 ? (
            <div className="h-[300px] w-full -ml-4">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                  <PolarGrid stroke="#444" />
                  <PolarAngleAxis dataKey="concept" tick={{ fill: '#888', fontSize: 11 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#444" tick={false} />
                  <Radar
                    name="Skill Level"
                    dataKey="score"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.4}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#2a2a3c', borderColor: '#444', borderRadius: '8px' }} 
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500 border border-dashed border-[#444] rounded-lg">
              Not enough data. Submit code first.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
