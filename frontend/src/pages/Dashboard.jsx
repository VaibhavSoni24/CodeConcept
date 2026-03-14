import React, { useEffect, useState, useMemo } from 'react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar
} from 'recharts';
import api, { getProfile, getUserSubmissions } from '../api';
import { Award, Target, Activity as ActivityIcon, Zap } from 'lucide-react';
import { 
  computeAverageConfidence, 
  computeMistakeRate, 
  buildConfidenceTimeline, 
  getUserRank 
} from '../utils/analytics';
import Loader from '../components/Loader';

function Dashboard({ user, credits }) {
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
          getProfile(user.id).catch(() => null),
          getUserSubmissions(user.id).catch(() => [])
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
  }, [user?.id]);

  // Aggregate stats using normalizeAnalysis
  const stats = useMemo(() => {
    const totalSubmissions = submissions.length;
    
    const avgConfidence = computeAverageConfidence(submissions);
    const errorRate = computeMistakeRate(submissions);
    const rank = getUserRank(avgConfidence);
    
    return {
      totalSubmissions,
      avgConfidencePercentage: Math.round(avgConfidence * 100),
      errorRatePercentage: Math.round(errorRate * 100),
      rank,
      languages: [...new Set(submissions.map(s => s.language).filter(Boolean))]
    };
  }, [submissions]);

  // History for LineChart based on submissions
  const historyData = useMemo(() => {
    return buildConfidenceTimeline(submissions);
  }, [submissions]);

  // Skill graph data filtered by lang (fallback safely)
  const availableSkillLangs = useMemo(() => {
    if (!profile?.skill_scores) return ['python'];
    const langs = [...new Set(profile.skill_scores.map(s => s.language || 'python'))];
    return langs.length > 0 ? langs : ['python'];
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
        concept: s.concept ? s.concept.replace(/_/g, " ") : "Unknown",
      }));
  }, [profile, activeSkillLang]);

  if (loading) return <Loader />;

  if (!loading && submissions.length === 0) {
    return (
      <div className="flex flex-col h-full overflow-y-auto w-full p-8 bg-[var(--bg-primary)]">
        <header className="mb-8 items-end">
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
            Learning Analytics Dashboard
          </h1>
        </header>
        <div className="flex flex-col items-center justify-center h-full w-full text-center slide-up mt-20">
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] p-12 rounded-xl max-w-lg shadow-lg">
             <Target className="text-gray-400 mx-auto mb-4" size={48} />
             <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">No submissions yet</h2>
             <p className="text-gray-400 mb-6">Run your first code analysis to see dashboard insights.</p>
          </div>
        </div>
      </div>
    );
  }

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
          <div className="p-3 bg-blue-500/10 rounded-lg"><ActivityIcon className="text-blue-500" size={24}/></div>
          <div>
            <p className="text-sm text-gray-400 font-semibold mb-1">Total Submissions</p>
            <p className="text-2xl font-bold">{stats.totalSubmissions}</p>
          </div>
        </div>

        <div className="card p-6 flex items-center gap-4 border-l-4 border-l-indigo-500">
          <div className="p-3 bg-indigo-500/10 rounded-lg"><Target className="text-indigo-500" size={24}/></div>
          <div title="Confidence measures how well the code follows correct programming concepts.">
            <p className="text-sm text-gray-400 font-semibold mb-1 cursor-help border-b border-dashed border-gray-500 inline-block">Average Confidence</p>
            <p className="text-2xl font-bold">{stats.avgConfidencePercentage}%</p>
          </div>
        </div>

        <div className="card p-6 flex items-center gap-4 border-l-4 border-l-red-500">
          <div className="p-3 bg-red-500/10 rounded-lg"><Zap className="text-red-500" size={24}/></div>
          <div title="Percentage of submissions containing conceptual mistakes.">
            <p className="text-sm text-gray-400 font-semibold mb-1 cursor-help border-b border-dashed border-gray-500 inline-block">Mistake Rate</p>
            <p className="text-2xl font-bold">{stats.errorRatePercentage}%</p>
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

        <div className={`card p-6 flex items-center gap-4 border-l-4 ${credits > 50 ? "border-l-emerald-500" : (credits >= 20 ? "border-l-yellow-500" : "border-l-red-500")}`}>
          <div className={`p-3 rounded-lg ${credits > 50 ? "bg-emerald-500/10" : (credits >= 20 ? "bg-yellow-500/10" : "bg-red-500/10")}`}><Award className={credits > 50 ? "text-emerald-500" : (credits >= 20 ? "text-yellow-500" : "text-red-500")} size={24}/></div>
          <div>
            <p className="text-sm text-gray-400 font-semibold mb-1">Credits Remaining</p>
            <p className={`text-2xl font-bold ${credits > 50 ? "text-emerald-500" : (credits >= 20 ? "text-yellow-500" : "text-red-500")}`}>{credits !== null ? credits : "..."}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Trajectory */}
        <div className="card p-6 lg:col-span-2 slide-up">
          <h3 className="text-lg font-bold mb-6 text-[var(--text-primary)]">Confidence Trajectory (Over Time)</h3>
          <div className="h-[300px] w-full">
            {historyData.length > 0 ? (
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
            ) : (
               <div className="flex items-center justify-center h-full text-gray-500 border border-dashed border-[#444] rounded-lg">
                Not enough data.
              </div>
            )}
          </div>
        </div>

        {/* Skill Radar */}
        <div className="card p-6 slide-up" style={{ animationDelay: '0.1s' }}>
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-[var(--text-primary)]">Current Concept Skills</h3>
            {availableSkillLangs.length > 0 && (
              <select
                value={activeSkillLang}
                onChange={(e) => setActiveSkillLang(e.target.value)}
                className="bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-primary)] px-3 py-1.5 rounded-lg text-sm outline-none w-32 focus:border-blue-500 transition-colors cursor-pointer"
              >
                {availableSkillLangs.map(lang => (
                  <option key={lang} value={lang}>{lang.charAt(0).toUpperCase() + lang.slice(1)}</option>
                ))}
              </select>
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
              Not enough profile data.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
