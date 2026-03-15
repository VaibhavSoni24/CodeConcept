import React, { useEffect, useState } from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from 'recharts';
import { BookOpen, GraduationCap, Youtube } from 'lucide-react';
import { getKnowledgeRecommendations, getGlobalKnowledgeSummary } from '../api';
import Loader from '../components/Loader';
import VideoRecommendations from '../components/VideoRecommendations';

const SUPPORTED_LANGUAGES = [
  { key: "python", label: "Python" },
  { key: "javascript", label: "JavaScript" },
  { key: "cpp", label: "C++" },
  { key: "java", label: "Java" },
  { key: "go", label: "Go" },
  { key: "rust", label: "Rust" },
];
const PIE_COLORS = ['#10b981', '#f59e0b', '#ef4444'];

function Knowledge({ user }) {
  const [userKnowledgeData, setUserKnowledgeData] = useState(null);
  const [globalKnowledgeData, setGlobalKnowledgeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('user');

  useEffect(() => {
    async function fetchKnowledge() {
      if (!user?.id) return;
      try {
        const [userData, globalData] = await Promise.all([
          getKnowledgeRecommendations(user.id),
          getGlobalKnowledgeSummary(),
        ]);
        setUserKnowledgeData(userData);
        setGlobalKnowledgeData(globalData);
      } catch (err) {
        console.error("Failed to fetch knowledge recommendations", err);
      } finally {
        setLoading(false);
      }
    }
    fetchKnowledge();
  }, [user]);

  if (loading) return <Loader />;

  const knowledgeData = viewMode === 'user' ? userKnowledgeData : globalKnowledgeData;

  // Destructure with fallbacks
  const {
    languages = {},
    concepts_learned = [],
    youtube_recommendations = [],
    language_summary = [],
    language_activity = [],
    mastery_distribution = [],
    top_concept_trend = [],
    global_users = 0,
  } = knowledgeData || {};

  const activityMap = Object.fromEntries(
    (language_activity || []).map((item) => [item.language, item.submissions])
  );

  const topConceptTrend = (top_concept_trend && top_concept_trend.length > 0)
    ? top_concept_trend
    : [...concepts_learned]
        .sort((a, b) => b.score - a.score)
        .slice(0, 10)
        .map((c, i) => ({ rank: i + 1, concept: c.concept, score: c.score, level: c.level }));

  const totalMasteryCount = mastery_distribution.reduce((sum, item) => sum + (item.value || 0), 0);

  const masteryPieData = mastery_distribution.map((item) => ({
    ...item,
    pct: totalMasteryCount > 0 ? Math.round(((item.value || 0) / totalMasteryCount) * 100) : 0,
  }));

  // Empty state guard
  if (!knowledgeData || (Object.keys(languages).length === 0 && concepts_learned.length === 0)) {
    return (
      <div className="flex flex-col h-full overflow-y-auto w-full p-8 bg-[var(--bg-primary)] items-center justify-center">
        <div className="card p-10 max-w-lg text-center flex flex-col items-center gap-4">
          <div className="w-16 h-16 bg-blue-500/10 rounded-full flex items-center justify-center mb-2">
            <BookOpen size={32} className="text-blue-500" />
          </div>
          <h2 className="text-2xl font-bold text-[var(--text-primary)]">Knowledge Hub</h2>
          <p className="text-[var(--text-secondary)]">
            Not enough submissions yet. Run more analyses to unlock personalized learning insights.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto w-full p-8 bg-[var(--bg-primary)]">
      <div className="max-w-7xl mx-auto w-full slide-up space-y-10">
        <header className="flex justify-between items-end border-b border-[var(--border)] pb-6">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500 flex items-center gap-3">
              <GraduationCap size={32} className="text-blue-500" />
              Knowledge Hub
            </h1>
            <p className="text-[var(--text-secondary)] mt-1">
              Analyze your cross-language skill tree and discover targeted learning tracks.
            </p>
          </div>
          <div className="flex items-center gap-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-1">
            <button
              className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-colors ${viewMode === 'user' ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
              onClick={() => setViewMode('user')}
            >
              User
            </button>
            <button
              className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-colors ${viewMode === 'global' ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
              onClick={() => setViewMode('global')}
            >
              Global
            </button>
          </div>
        </header>

        <section className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card p-5">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">View Mode</p>
            <p className="text-xl font-bold mt-2">{viewMode === 'user' ? 'User Analytics' : 'Global Analytics'}</p>
          </div>
          <div className="card p-5">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Languages Covered</p>
            <p className="text-xl font-bold mt-2">{SUPPORTED_LANGUAGES.length}</p>
          </div>
          <div className="card p-5">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Concepts Tracked</p>
            <p className="text-xl font-bold mt-2">{concepts_learned.length}</p>
          </div>
          <div className="card p-5">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Global Users</p>
            <p className="text-xl font-bold mt-2">{viewMode === 'global' ? global_users : '—'}</p>
          </div>
        </section>

        <section className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="card p-5 h-[360px]">
            <h3 className="text-lg font-bold mb-4">Language Average Skill</h3>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={language_summary} margin={{ top: 8, right: 16, left: 0, bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="language" angle={-20} textAnchor="end" height={50} tick={{ fill: 'var(--text-secondary)' }} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-secondary)' }} />
                <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }} />
                <Bar dataKey="avg_score" fill="var(--accent)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card p-5 h-[360px]">
            <h3 className="text-lg font-bold mb-4">Language Activity (Submissions)</h3>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={language_activity} margin={{ top: 8, right: 16, left: 0, bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="language" angle={-20} textAnchor="end" height={50} tick={{ fill: 'var(--text-secondary)' }} />
                <YAxis tick={{ fill: 'var(--text-secondary)' }} />
                <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }} />
                <Bar dataKey="submissions" fill="#06b6d4" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card p-5 h-[360px]">
            <h3 className="text-lg font-bold mb-4">Mastery Distribution</h3>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={masteryPieData}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={110}
                  label={({ name, pct }) => `${name}: ${pct}%`}
                >
                  {masteryPieData.map((entry, index) => (
                    <Cell key={`cell-${entry.name}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="card p-5 h-[360px]">
            <h3 className="text-lg font-bold mb-4">Top Concept Trend</h3>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={topConceptTrend} margin={{ top: 8, right: 16, left: 0, bottom: 50 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="concept"
                  angle={-20}
                  textAnchor="end"
                  height={65}
                  interval={0}
                  tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-secondary)' }} />
                <Tooltip
                  formatter={(value, _name, item) => [`${value}%`, item?.payload?.level || 'Mastery']}
                  labelFormatter={(label) => `Concept: ${label}`}
                  contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
                />
                <Line type="monotone" dataKey="score" stroke="#22c55e" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* SECTION 1: Language Skill Graphs */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 border-b border-[var(--border)] pb-2">
            <h2 className="text-xl font-bold text-[var(--text-primary)]">Language Skill Graphs</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {SUPPORTED_LANGUAGES.map((lang) => {
              const langData = languages[lang.key]?.concept_scores || [];
              const hasData = langData.length > 0;
              const submissionCount = activityMap[lang.key] || 0;
              
              return (
                <div key={lang.key} className="card p-6 flex flex-col h-[380px]">
                  <h3 className="text-lg font-bold text-[var(--text-primary)] capitalize mb-4 text-center">
                    {lang.label}
                  </h3>
                  <div className="flex-1 flex items-center justify-center w-full">
                    {hasData ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={langData}>
                          <PolarGrid stroke="var(--border)" />
                          <PolarAngleAxis 
                            dataKey="concept" 
                            tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} 
                          />
                          <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="var(--text-muted)" tick={false} />
                          <Radar
                            name="Skill"
                            dataKey="score"
                            stroke="var(--accent)"
                            fill="var(--accent)"
                            fillOpacity={0.4}
                          />
                        </RadarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="text-[var(--text-muted)] italic text-sm text-center">
                        {submissionCount > 0
                          ? `Submissions: ${submissionCount}. No skill vectors yet for ${lang.label}.`
                          : `No code evaluated in ${lang.label} yet.`}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* SECTION 2: Concepts Learned Table */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 border-b border-[var(--border)] pb-2">
            <h2 className="text-xl font-bold text-[var(--text-primary)]">Concepts Learned</h2>
          </div>
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-[var(--text-secondary)]">
                <thead className="text-xs text-[var(--text-primary)] uppercase bg-[var(--bg-secondary)] border-b border-[var(--border)]">
                  <tr>
                    <th className="px-6 py-4">Concept</th>
                    <th className="px-6 py-4 w-1/3">Mastery Progress</th>
                    <th className="px-6 py-4 text-right">Score</th>
                    <th className="px-6 py-4 text-right">Level</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)] bg-[var(--bg-card)]">
                  {concepts_learned.map((itm, idx) => {
                    let levelColor = "text-indigo-400";
                    let barColor = "bg-indigo-500";
                    if (itm.level === "Strong") {
                      levelColor = "text-emerald-400";
                      barColor = "bg-emerald-500";
                    } else if (itm.level === "Needs Practice") {
                      levelColor = "text-amber-400";
                      barColor = "bg-amber-500";
                    }

                    return (
                      <tr key={idx} className="hover:bg-[var(--bg-secondary)] transition-colors">
                        <td className="px-6 py-4 font-medium text-[var(--text-primary)]">{itm.concept}</td>
                        <td className="px-6 py-4">
                          <div className="w-full bg-[var(--border)] rounded-full h-2.5">
                            <div 
                              className={`${barColor} h-2.5 rounded-full transition-all duration-500`} 
                              style={{ width: `${itm.score}%` }}
                            ></div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right font-medium">{itm.score}%</td>
                        <td className={`px-6 py-4 text-right font-bold ${levelColor}`}>{itm.level}</td>
                      </tr>
                    );
                  })}
                  {concepts_learned.length === 0 && (
                    <tr>
                      <td colSpan="4" className="px-6 py-8 text-center text-[var(--text-muted)] italic">
                        Evaluate more code snippets to establish your concept mastery timeline.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {viewMode === 'user' && (
          <section className="space-y-6">
            <div className="flex items-center gap-2 border-b border-[var(--border)] pb-2">
              <h2 className="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
                <Youtube className="text-red-500" size={24} />
                Recommended Learning Videos
              </h2>
            </div>
            <VideoRecommendations videos={youtube_recommendations} />
          </section>
        )}
        
      </div>
    </div>
  );
}

export default Knowledge;
