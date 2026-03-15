import React, { useEffect, useMemo, useState } from "react";
import {
  getBillingPlans,
  getBillingMetrics,
  getUserSubscription,
  subscribePlan,
  topupCredits,
} from "../api";
import Loader from "../components/Loader";

function Shop({ user, credits, setCredits }) {
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState(null);
  const [plans, setPlans] = useState({});
  const [creditPacks, setCreditPacks] = useState({});
  const [subscription, setSubscription] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [message, setMessage] = useState("");

  const loadData = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      const [planData, subData, metricData] = await Promise.all([
        getBillingPlans(),
        getUserSubscription(user.id),
        getBillingMetrics(),
      ]);
      setPlans(planData?.plans || {});
      setCreditPacks(planData?.credit_packs || {});
      setSubscription(subData || null);
      setMetrics(metricData || null);
    } catch (err) {
      console.error("Failed to load shop data", err);
      setMessage("Could not load billing data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user?.id]);

  const handleSubscribe = async (planKey) => {
    if (!user?.id) return;
    try {
      setBusyKey(`plan-${planKey}`);
      const res = await subscribePlan(user.id, planKey);
      if (typeof res?.credits === "number" && typeof setCredits === "function") {
        setCredits(res.credits);
      }
      setMessage(res?.message || "Plan updated.");
      await loadData();
    } catch (err) {
      console.error("Plan update failed", err);
      setMessage(err?.response?.data?.detail || "Plan update failed.");
    } finally {
      setBusyKey(null);
    }
  };

  const handleTopup = async (packKey) => {
    if (!user?.id) return;
    try {
      setBusyKey(`pack-${packKey}`);
      const res = await topupCredits(user.id, packKey);
      if (typeof res?.credits === "number" && typeof setCredits === "function") {
        setCredits(res.credits);
      }
      setMessage(res?.message || "Credits added.");
      await loadData();
    } catch (err) {
      console.error("Top-up failed", err);
      setMessage(err?.response?.data?.detail || "Top-up failed.");
    } finally {
      setBusyKey(null);
    }
  };

  const planCards = useMemo(() => Object.entries(plans), [plans]);
  const packCards = useMemo(() => Object.entries(creditPacks), [creditPacks]);
  if (loading) return <Loader />;

  return (
    <div className="flex flex-col h-full overflow-y-auto w-full p-8 bg-[var(--bg-primary)]">
      <header className="mb-8">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-emerald-500">
          Monetization Hub
        </h1>
        <p className="text-gray-400 mt-2">
          Simulated subscriptions and credit purchases. No real payment is processed.
        </p>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card p-6 border border-[var(--border)]">
          <p className="text-xs uppercase tracking-wide text-[var(--text-secondary)]">Current Plan</p>
          <p className="text-2xl font-bold mt-2 capitalize text-[var(--text-primary)]">{subscription?.plan_key || "free"}</p>
          <p className="text-sm text-gray-400 mt-2">Status: {subscription?.status || "active"}</p>
        </div>
        <div className="card p-6 border border-[var(--border)]">
          <p className="text-xs uppercase tracking-wide text-[var(--text-secondary)]">Credits Balance</p>
          <p className="text-2xl font-bold mt-2 text-emerald-400">{typeof credits === "number" ? credits : "..."}</p>
          <p className="text-sm text-gray-400 mt-2">Used to run analysis jobs.</p>
        </div>
      </section>

      {message && (
        <div className="mb-6 card p-4 border border-cyan-500/40 text-cyan-300">
          {message}
        </div>
      )}

      <section className="mb-12">
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Subscription Plans</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
          {planCards.map(([planKey, plan]) => {
            const isCurrent = subscription?.plan_key === planKey;
            return (
              <div
                key={planKey}
                className={`card p-6 border transition-colors ${isCurrent ? "border-emerald-500" : "border-[var(--border)] hover:border-cyan-500"}`}
              >
                <p className="text-xs uppercase tracking-wide text-[var(--text-secondary)]">{plan.name}</p>
                <p className="text-3xl font-bold text-[var(--text-primary)] mt-2">${plan.price_monthly}<span className="text-base text-gray-400">/mo</span></p>
                <p className="text-sm text-gray-400 mt-2">{plan.credits_per_month} credits per month</p>
                <p className="text-sm text-gray-400">{plan.included_analyses} included analyses</p>
                <ul className="text-xs text-gray-300 mt-4 space-y-1 min-h-[70px]">
                  {(plan.features || []).map((f) => <li key={f}>- {f}</li>)}
                </ul>
                <button
                  onClick={() => handleSubscribe(planKey)}
                  disabled={isCurrent || busyKey === `plan-${planKey}`}
                  className={`w-full mt-5 py-2 rounded font-semibold transition-colors ${isCurrent ? "bg-emerald-600/30 text-emerald-300 cursor-not-allowed" : "bg-cyan-600 hover:bg-cyan-500 text-white"}`}
                >
                  {isCurrent ? "Current Plan" : busyKey === `plan-${planKey}` ? "Updating..." : "Switch Plan"}
                </button>
              </div>
            );
          })}
        </div>
      </section>

      <section className="mb-12">
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Credit Packs</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {packCards.map(([packKey, pack], i) => (
            <div
              key={packKey}
              className="card p-6 border border-[var(--border)] hover:border-emerald-500 transition-colors"
              style={{ animationDelay: `${i * 0.06}s` }}
            >
              <h3 className="text-lg font-bold text-[var(--text-primary)]">{pack.name}</h3>
              <p className="text-3xl font-extrabold mt-2 text-emerald-400">${pack.price}</p>
              <p className="text-sm text-gray-400 mt-2">+{pack.credits} credits</p>
              <button
                onClick={() => handleTopup(packKey)}
                disabled={busyKey === `pack-${packKey}`}
                className="w-full mt-6 py-2 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-colors disabled:opacity-70"
              >
                {busyKey === `pack-${packKey}` ? "Processing..." : "Buy Pack"}
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default Shop;
