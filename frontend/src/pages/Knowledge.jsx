import React, { useEffect, useState } from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { BookOpen, GraduationCap, Youtube } from 'lucide-react';
import { getKnowledgeRecommendations } from '../api';
import Loader from '../components/Loader';
import VideoRecommendations from '../components/VideoRecommendations';

const SUPPORTED_LANGUAGES = ["python", "javascript", "c++", "java", "go", "rust"];

function Knowledge({ user }) {
  const [knowledgeData, setKnowledgeData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchKnowledge() {
      if (!user?.id) return;
      try {
        const data = await getKnowledgeRecommendations(user.id);
        setKnowledgeData(data);
      } catch (err) {
        console.error("Failed to fetch knowledge recommendations", err);
      } finally {
        setLoading(false);
      }
    }
    fetchKnowledge();
  }, [user]);

  if (loading) return <Loader />;

  // Destructure with fallbacks
  const { languages = {}, concepts_learned = [], youtube_recommendations = [] } = knowledgeData || {};

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
        </header>

        {/* SECTION 1: Language Skill Graphs */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 border-b border-[var(--border)] pb-2">
            <h2 className="text-xl font-bold text-[var(--text-primary)]">Language Skill Graphs</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {SUPPORTED_LANGUAGES.map((lang) => {
              const langData = languages[lang]?.concept_scores || [];
              const hasData = langData.length > 0;
              
              return (
                <div key={lang} className="card p-6 flex flex-col h-[380px]">
                  <h3 className="text-lg font-bold text-[var(--text-primary)] capitalize mb-4 text-center">
                    {lang}
                  </h3>
                  <div className="flex-1 flex items-center justify-center w-full">
                    {hasData ? (
                      <ResponsiveContainer w="100%" height="100%">
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
                        No code evaluated in {lang} yet.
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

        {/* SECTION 3: YouTube Recommendation Engine */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 border-b border-[var(--border)] pb-2">
            <h2 className="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
               <Youtube className="text-red-500" size={24} />
               Recommended Learning Videos
            </h2>
          </div>
          <VideoRecommendations videos={youtube_recommendations} />
        </section>
        
      </div>
    </div>
  );
}

export default Knowledge;
