import React, { useEffect, useState } from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { getProfile, getUserSubmissions, getMe } from '../api';
import { User, Mail, Calendar, Award } from 'lucide-react';
import { computeAverageConfidence, getUserRank } from '../utils/analytics';
import Loader from '../components/Loader';

function Profile({ user, credits }) {
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSkillLang, setActiveSkillLang] = useState('python');
  const [computedLevel, setComputedLevel] = useState(user?.level || 'Beginner');

  const [fullUser, setFullUser] = useState(user);

  useEffect(() => {
    if (user?.id) {
      Promise.all([
        getProfile(user.id),
        getUserSubmissions(user.id),
        getMe()
      ]).then(([data, subs, meData]) => {
        setProfileData(data);
        const avg = computeAverageConfidence(subs);
        setComputedLevel(getUserRank(avg));
        if (meData) setFullUser(meData);
      }).catch(console.error)
      .finally(() => setLoading(false));
    }
  }, [user?.id]);

  const availableSkillLangs = profileData?.skill_scores 
    ? [...new Set(profileData.skill_scores.map(s => s.language || 'python'))] 
    : [];

  useEffect(() => {
    if (availableSkillLangs.length > 0 && !availableSkillLangs.includes(activeSkillLang)) {
      setActiveSkillLang(availableSkillLangs[0]);
    }
  }, [availableSkillLangs, activeSkillLang]);

  const radarData = profileData?.skill_scores
    ? profileData.skill_scores
        .filter(s => (s.language || 'python') === activeSkillLang)
        .map(s => ({
          ...s,
          concept: s.concept ? s.concept.replace(/_/g, " ") : "Unknown",
        }))
    : [];

  const joinDate = fullUser?.created_at ? new Date(fullUser.created_at).toLocaleDateString() : 'Unknown';

  if (loading) return <Loader />;

  return (
    <div className="flex flex-col h-full overflow-y-auto w-full p-8 bg-[var(--bg-primary)]">
      <div className="max-w-5xl mx-auto w-full slide-up space-y-8">
        <header className="flex justify-between items-end border-b border-[var(--border)] pb-6">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
              Developer Profile
            </h1>
            <p className="text-[var(--text-secondary)] mt-1">Manage your account and review overarching skills.</p>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="card md:col-span-1 p-6 flex flex-col items-center text-center space-y-4">
            <div className="w-24 h-24 bg-gradient-to-tr from-indigo-500 to-blue-500 rounded-full flex items-center justify-center shadow-[0_0_20px_var(--accent-glow)] mb-2">
              <span className="text-3xl font-bold text-white uppercase">{user?.name?.charAt(0) || '?'}</span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-[var(--text-primary)]">{user?.name || 'Developer'}</h2>
              <div className="flex items-center justify-center gap-2 text-sm text-[var(--text-secondary)] mt-1">
                <Mail size={14} /> {user?.email || 'No email provided'}
              </div>
            </div>

            <div className="w-full h-px bg-[var(--border)] my-4"></div>

            <div className="w-full space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-[var(--text-muted)] flex items-center gap-2"><Award size={14}/> Base Level</span>
                <span className="font-semibold text-[var(--text-primary)] capitalize">{computedLevel}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-[var(--text-muted)] flex items-center gap-2"><Award size={14}/> Credits Balance</span>
                <span className="font-semibold" style={{ color: credits !== null ? (credits > 50 ? '#10b981' : credits >= 20 ? '#eab308' : '#ef4444') : 'inherit' }}>
                  {credits !== null ? credits : "..."}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-[var(--text-muted)] flex items-center gap-2"><Calendar size={14}/> Joined</span>
                <span className="font-semibold text-[var(--text-primary)]">{joinDate}</span>
              </div>
            </div>
          </div>

          <div className="card md:col-span-2 p-6 flex flex-col">
            <div className="flex justify-between items-center mb-6 border-b border-[var(--border)] pb-4">
              <h3 className="text-lg font-bold text-[var(--text-primary)]">
                Aggregate Concept Mastery
              </h3>
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
            
            <div className="flex-1 flex items-center justify-center min-h-[300px]">
              {radarData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                    <PolarGrid stroke="var(--border)" />
                    <PolarAngleAxis dataKey="concept" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
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
                <p className="text-[var(--text-muted)] italic">No analysis data yet. Try submitting some code.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile;
