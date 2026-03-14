export function normalizeAnalysis(submission) {
  if (!submission) return { confidence: 0, mistakes: [], complexity: {} };
  
  // Handle stringified JSON if it comes back raw
  let result = null;
  if (typeof submission.analysis_result === 'string') {
    try {
      result = JSON.parse(submission.analysis_result);
    } catch (e) {
      result = null;
    }
  } else {
    result = submission.analysis_result;
  }

  return {
    confidence: result?.confidence || 0,
    mistakes: result?.mistakes || [],
    complexity: result?.complexity || {}
  };
}
