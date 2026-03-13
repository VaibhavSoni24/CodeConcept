import { useState } from "react";

export default function AuthPage({ onAuth }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [level, setLevel] = useState("beginner");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const toggleMode = () => {
    setMode((m) => (m === "login" ? "register" : "login"));
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const { registerUser, loginUser } = await import("../api");
      let data;
      if (mode === "register") {
        data = await registerUser(name, email, password, level);
      } else {
        data = await loginUser(email, password);
      }
      // data = { access_token, token_type, user }
      localStorage.setItem("cc_token", data.access_token);
      localStorage.setItem("cc_user", JSON.stringify(data.user));
      onAuth(data.user, data.access_token);
    } catch (err) {
      const detail =
        err.response?.data?.detail ||
        (mode === "register"
          ? "Registration failed. Please try again."
          : "Invalid email or password.");
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-backdrop">
      {/* ambient glow handled by body::before/after */}
      <div className="auth-card slide-down">
        {/* Logo */}
        <div className="auth-logo">
          <span className="auth-logo-icon">✦</span>
          <h1>CodeConcept</h1>
        </div>
        <p className="auth-subtitle">
          {mode === "login"
            ? "Sign in to start learning"
            : "Create your learner account"}
        </p>

        {/* Error */}
        {error && <div className="auth-error">{error}</div>}

        {/* Form */}
        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === "register" && (
            <label className="auth-field">
              <span>Name</span>
              <input
                id="auth-name"
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                minLength={2}
                autoComplete="name"
              />
            </label>
          )}

          <label className="auth-field">
            <span>Email</span>
            <input
              id="auth-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </label>

          <label className="auth-field">
            <span>Password</span>
            <input
              id="auth-password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              autoComplete={mode === "register" ? "new-password" : "current-password"}
            />
          </label>

          {mode === "register" && (
            <label className="auth-field">
              <span>Experience Level</span>
              <select
                id="auth-level"
                value={level}
                onChange={(e) => setLevel(e.target.value)}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </label>
          )}

          <button
            id="auth-submit"
            type="submit"
            className="btn auth-btn"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" /> {mode === "login" ? "Signing in…" : "Creating account…"}
              </>
            ) : mode === "login" ? (
              "Sign In"
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        {/* Toggle */}
        <p className="auth-toggle">
          {mode === "login" ? (
            <>
              Don't have an account?{" "}
              <button type="button" onClick={toggleMode}>
                Register
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button type="button" onClick={toggleMode}>
                Sign In
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
