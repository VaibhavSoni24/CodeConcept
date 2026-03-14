import { normalizeAnalysis } from './normalizeAnalysis';

export function computeAverageConfidence(submissions) {
  if (!submissions || submissions.length === 0) return 0;
  
  const confidenceValues = submissions
    .map(s => normalizeAnalysis(s).confidence)
    .filter(v => typeof v === "number" && !isNaN(v));
    
  if (confidenceValues.length === 0) return 0;
  
  const total = confidenceValues.reduce((a, b) => a + b, 0);
  return total / confidenceValues.length;
}

export function computeMistakeRate(submissions) {
  if (!submissions || submissions.length === 0) return 0;
  
  const submissionsWithMistakes = submissions.filter(s => {
    const parsed = normalizeAnalysis(s);
    return parsed.mistakes && parsed.mistakes.length > 0;
  });
  
  return submissionsWithMistakes.length / submissions.length;
}

export function buildConfidenceTimeline(submissions) {
  if (!submissions || submissions.length === 0) return [];
  
  const sortedSubs = [...submissions].sort((a,b) => new Date(a.timestamp || a.created_at) - new Date(b.timestamp || b.created_at));
  
  return sortedSubs.map((s, index) => {
    const parsed = normalizeAnalysis(s);
    const conf = Math.round((parsed.confidence || 0) * 100);
    return {
      name: `Sub ${index + 1}`,
      date: new Date(s.timestamp || s.created_at).toLocaleDateString(),
      confidence: conf,
      mastery: Math.min(100, Math.round(conf * 1.2)) // proxy for visual
    };
  });
}

export function getUserRank(avgConfidence) {
  if (avgConfidence < 0.4) return "Beginner";
  if (avgConfidence < 0.75) return "Intermediate";
  return "Advanced";
}
