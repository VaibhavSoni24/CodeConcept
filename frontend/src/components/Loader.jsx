import React from 'react';

function Loader() {
  return (
    <div className="flex justify-center items-center h-full w-full p-10">
      <div className="spinner w-8 h-8 rounded-full border-4 border-t-[var(--accent)] border-r-[var(--accent)] border-b-transparent border-l-transparent animate-spin"></div>
    </div>
  );
}

export default Loader;
