import React, { useState, useMemo, useEffect } from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

function SkillRadarChart({ skillScores }) {
  const [activeLang, setActiveLang] = useState('python');

  const languages = useMemo(() => {
    if (!skillScores) return [];
    return [...new Set(skillScores.map(s => s.language || 'python'))];
  }, [skillScores]);

  useEffect(() => {
    if (languages.length > 0 && !languages.includes(activeLang)) {
      setActiveLang(languages[0]);
    }
  }, [languages, activeLang]);

  if (!skillScores || skillScores.length === 0) {
    return (
      <div className="card card-glow">
        <div className="card-header">
          <h2>
            <span className="card-icon purple">🎯</span>
            Skill Graph
          </h2>
        </div>
        <p className="feedback-empty">
          Submit more code to build your skill graph.
        </p>
      </div>
    );
  }

  const data = skillScores
    .filter((s) => (s.language || 'python') === activeLang)
    .map((s) => ({
      concept: s.concept.replace(/_/g, " "),
      score: s.score,
      fullMark: 100,
    }));

  return (
    <div className="card card-glow fade-in">
      <div className="card-header flex justify-between items-center mb-2">
        <h2 className="flex items-center gap-2">
          <span className="card-icon purple">🎯</span>
          Skill Graph
        </h2>
        {languages.length > 0 && (
          <div className="flex gap-1">
            {languages.map(l => (
              <button
                key={l}
                onClick={() => setActiveLang(l)}
                className={`px-2 py-1 text-[0.7rem] uppercase font-bold rounded ${
                  activeLang === l 
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
      <div className="radar-container">
        <ResponsiveContainer width="100%" height={280}>
          <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
            <PolarGrid stroke="rgba(100,116,139,0.2)" />
            <PolarAngleAxis
              dataKey="concept"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: "#64748b", fontSize: 10 }}
              tickCount={5}
            />
            <Radar
              name="Mastery"
              dataKey="score"
              stroke="#6366f1"
              fill="rgba(99,102,241,0.25)"
              fillOpacity={0.6}
              strokeWidth={2}
            />
            <Tooltip
              contentStyle={{
                background: "#1e293b",
                border: "1px solid rgba(99,102,241,0.3)",
                borderRadius: "8px",
                color: "#f1f5f9",
                fontSize: "0.82rem",
              }}
              formatter={(value) => [`${value}%`, "Score"]}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default SkillRadarChart;
