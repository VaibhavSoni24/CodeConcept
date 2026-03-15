import React from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';

function FlowGraphPanel({ flowGraph, language }) {
  if (!flowGraph || !flowGraph.nodes || flowGraph.nodes.length === 0) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-bold mb-4">Control Flow Graph</h3>
        <p className="text-gray-500">
          No Control Flow Graph available yet. Click Analyze (Run is only execution), or check parser support for {language || "this language"}.
        </p>
      </div>
    );
  }

  const initialNodes = flowGraph.nodes.map((n, i) => ({
    id: String(n.id),
    data: { label: n.label || n.type },
    position: { x: 250, y: i * 100 },
    style: { 
        background: '#2a2a3c', 
        color: '#fff', 
        border: '1px solid #444', 
        borderRadius: '8px',
        padding: '10px'
    }
  }));

  const initialEdges = flowGraph.edges.map((e, i) => ({
    id: `e${e.from}-${e.to}-${i}`,
    source: String(e.from),
    target: String(e.to),
    animated: true,
    style: { stroke: '#10b981' }, 
  }));

  return (
    <div className="card w-full h-[500px] overflow-hidden flex flex-col">
      <div className="bg-[#2a2a3c] px-4 py-3 border-b border-[#444]">
        <h3 className="font-semibold text-white m-0">Control Flow Graph</h3>
      </div>
      <div className="flex-1 w-full bg-[#1e1e2d]">
        <ReactFlow 
          defaultNodes={initialNodes} 
          defaultEdges={initialEdges} 
          fitView
        >
          <Background color="#333" gap={16} />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}

export default FlowGraphPanel;
