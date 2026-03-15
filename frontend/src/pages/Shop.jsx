import React from "react";

function Shop() {
  const handlePurchase = () => {
    alert("Payment integration coming soon");
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto w-full p-8 bg-[var(--bg-primary)]">
      <header className="mb-8 items-end">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
          Shop
        </h1>
        <p className="text-gray-400 mt-2">Recharge your credits or upgrade your plan for unlimited analyses.</p>
      </header>

      <section className="mb-12">
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Plans</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[{ name: "Monthly Plan", price: "₹199/month" }, { name: "Yearly Plan", price: "₹1999/year" }, { name: "Lifetime Plan", price: "₹4999" }].map(plan => (
            <div key={plan.name} className="card p-6 border border-[var(--border)] flex flex-col items-center justify-between text-center min-h-[200px] slide-up hover:border-blue-500 transition-colors">
              <div>
                <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                <p className="text-2xl text-blue-400 font-extrabold mb-4">{plan.price}</p>
                <p className="text-gray-400 text-sm">Unlimited analyses</p>
              </div>
              <button 
                onClick={handlePurchase}
                className="w-full mt-6 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors"
              >
                Buy Now
              </button>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Credit Packs</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[{ credits: 1000, price: "₹199" }, { credits: 3000, price: "₹499" }, { credits: 10000, price: "₹1499" }].map(pack => (
            <div key={pack.credits} className="card p-6 border border-[var(--border)] flex flex-col items-center justify-between text-center min-h-[180px] slide-up hover:border-indigo-500 transition-colors" style={{ animationDelay: '0.1s' }}>
              <div>
                <h3 className="text-lg font-bold text-gray-200 mb-2">{pack.credits} Credits</h3>
                <p className="text-xl text-indigo-400 font-extrabold">{pack.price}</p>
              </div>
              <button 
                onClick={handlePurchase}
                className="w-full mt-6 py-2 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors"
              >
                Buy
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default Shop;
