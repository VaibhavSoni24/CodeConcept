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
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
            {youtube_recommendations.map((vid, idx) => {
              const isSearchLink = !vid.video_id;
              return (
                <a
                  key={idx}
                  href={vid.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="card overflow-hidden group hover:-translate-y-1 transition-transform duration-200 block"
                >
                  <div className="relative aspect-video bg-gradient-to-br from-gray-900 to-gray-800 border-b border-[var(--border)] flex items-center justify-center">
                    {!isSearchLink ? (
                      <>
                        <img
                          src={vid.thumbnail}
                          alt={vid.title}
                          className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity absolute inset-0"
                          onError={(e) => { e.currentTarget.style.display = 'none'; }}
                        />
                        <div className="absolute inset-0 flex items-center justify-center bg-black/40 group-hover:bg-black/20 transition-colors">
                          <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" className="w-4 h-4 ml-0.5"><path d="M8 5v14l11-7z"/></svg>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="flex flex-col items-center justify-center gap-2 p-2 text-center">
                        <div className="w-8 h-8 bg-red-600/80 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" className="w-4 h-4"><path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
                        </div>
                        <span className="text-[0.6rem] text-gray-400">Search YouTube</span>
                      </div>
                    )}
                    <div className="absolute top-1 right-1 bg-indigo-600/90 text-white text-[0.55rem] uppercase font-bold px-1.5 py-0.5 rounded">
                      {vid.concept}
                    </div>
                  </div>
                  <div className="p-3">
                    <h4 className="text-xs font-semibold text-[var(--text-primary)] line-clamp-2 leading-tight mb-1 group-hover:text-indigo-400 transition-colors">
                      {vid.title}
                    </h4>
                    <span className="text-[0.65rem] text-[var(--text-secondary)]">{vid.channel}</span>
                  </div>
                </a>
              );
            })}
          </div>
        </section>
        
      </div>
    </div>
  );
}

export default Knowledge;
