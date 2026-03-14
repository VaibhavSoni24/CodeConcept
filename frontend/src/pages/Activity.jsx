import React, { useEffect, useState } from 'react';
import { getUserSubmissions, getNotes, createNote } from '../api';
import { Play, Code, Clock, BookOpen, Send } from 'lucide-react';
import CodeEditor from '../components/CodeEditor';

function Activity({ user }) {
  const [submissions, setSubmissions] = useState([]);
  const [allNotes, setAllNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSub, setSelectedSub] = useState(null);
  const [newNote, setNewNote] = useState("");
  const [isNoteLoading, setIsNoteLoading] = useState(false);

  useEffect(() => {
    async function loadData() {
      if (!user?.id) return;
      try {
        const [subData, notesData] = await Promise.all([
          getUserSubmissions(user.id),
          getNotes(user.id)
        ]);
        setSubmissions(subData);
        setAllNotes(notesData);
        if (subData.length > 0) setSelectedSub(subData[0]);
      } catch (err) {
        console.error("Failed to load activity data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [user]);

  const handleAddNote = async () => {
    if (!newNote.trim() || !selectedSub) return;
    setIsNoteLoading(true);
    try {
      const res = await createNote(selectedSub.id, newNote);
      setAllNotes([...allNotes, {
        id: res.note_id,
        submission_id: selectedSub.id,
        content: newNote,
        timestamp: new Date().toISOString()
      }]);
      setNewNote("");
    } catch (err) {
      console.error("Error creating note", err);
    } finally {
      setIsNoteLoading(false);
    }
  };

  if (loading) return <div className="p-10 flex justify-center"><div className="spinner w-8 h-8" /></div>;

  const currentNotes = allNotes.filter(n => n.submission_id === selectedSub?.id);

  return (
    <div className="flex h-full w-full bg-[#151521] overflow-hidden">
      {/* Left Sidebar: Submission List */}
      <div className="w-1/3 border-r border-[#333] flex flex-col h-full bg-[#1a1a24]">
        <div className="p-6 border-b border-[#333]">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Clock className="text-indigo-400" />
            Activity History
          </h2>
          <p className="text-sm text-gray-400 mt-1">Review your past code iterations, notes, and AI feedback.</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {submissions.length === 0 ? (
            <div className="text-center text-gray-500 py-10">No past activity found.</div>
          ) : (
            submissions.map(sub => (
              <div 
                key={sub.id} 
                onClick={() => setSelectedSub(sub)}
                className={`p-4 rounded-xl cursor-pointer transition-all border ${
                  selectedSub?.id === sub.id 
                    ? "bg-[#2a2a3c] border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.1)]" 
                    : "bg-[#1e1e2d] border-[#333] hover:border-[#555]"
                }`}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold px-2 py-1 bg-gray-800 rounded text-gray-300">
                    {sub.language.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(sub.timestamp).toLocaleString(undefined, {
                      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                    })}
                  </span>
                </div>
                <div className="text-sm font-semibold text-gray-200 mt-2 truncate w-full">
                  {sub.result}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right Content: Details */}
      <div className="flex-1 flex flex-col h-full p-6 overflow-y-auto">
        {selectedSub ? (
          <div className="slide-up max-w-4xl w-full mx-auto space-y-6">
            <header className="flex justify-between items-end border-b border-[#333] pb-4">
              <div>
                <h1 className="text-2xl font-bold text-white">Submission #{selectedSub.id}</h1>
                <p className="text-gray-400 text-sm mt-1">
                  Analysis detected: <span className="text-indigo-400">{selectedSub.result}</span>
                </p>
              </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="card h-full">
                <div className="card-header bg-[#222232] border-b border-[#333] flex items-center gap-2">
                  <Code size={16} className="text-blue-400" />
                  <h3 className="m-0 font-semibold text-white">Source Code</h3>
                </div>
                <div className="h-[400px]">
                  <CodeEditor 
                    code={selectedSub.code} 
                    language={selectedSub.language === "python" ? "python" : selectedSub.language}
                    readOnly={true}
                  />
                </div>
              </div>

              <div className="flex flex-col gap-6">
                <div className="card flex-1">
                  <div className="card-header bg-[#222232] border-b border-[#333]">
                    <h3 className="m-0 font-semibold text-white">AI Diagnostic Feedback</h3>
                  </div>
                  <div className="p-6">
                    <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
                      {selectedSub.analysis_result || "No detailed feedback recorded for this execution."}
                    </p>
                  </div>
                </div>

                {/* Notes Section */}
                <div className="card flex-1 flex flex-col">
                  <div className="card-header bg-[#222232] border-b border-[#333] flex items-center gap-2">
                    <BookOpen size={16} className="text-amber-400" />
                    <h3 className="m-0 font-semibold text-white">My Notes (Markdown)</h3>
                  </div>
                  <div className="p-4 flex-1 flex flex-col bg-[#1a1a24]">
                    <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                      {currentNotes.length === 0 ? (
                        <p className="text-gray-500 text-sm italic">No notes for this submission.</p>
                      ) : (
                        currentNotes.map(note => (
                          <div key={note.id} className="p-3 bg-[#2a2a3c] rounded-lg text-sm text-gray-300 whitespace-pre-wrap border border-[#444]">
                            {note.content}
                          </div>
                        ))
                      )}
                    </div>
                    <div className="flex gap-2">
                      <textarea
                        className="flex-1 bg-[#151521] border border-[#333] rounded-lg p-3 text-sm text-gray-200 resize-none outline-none focus:border-indigo-500"
                        placeholder="Add a reflective note on what you learned or struggled with..."
                        rows={2}
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                      />
                      <button 
                        className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-4 flex items-center justify-center transition-colors disabled:opacity-50"
                        onClick={handleAddNote}
                        disabled={isNoteLoading || !newNote.trim()}
                      >
                        {isNoteLoading ? <span className="spinner w-4 h-4"/> : <Send size={16} />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500">
            Select a submission from the history to view details.
          </div>
        )}
      </div>
    </div>
  );
}

export default Activity;
