import React, { useEffect, useState, useCallback } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  applyNodeChanges, 
  applyEdgeChanges,
  MarkerType 
} from 'reactflow';
import 'reactflow/dist/style.css';
import api from '../api';

const nodeTypes = {}; 

function ASTGraph({ code, language }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchAST = async () => {
    if (!code) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.post("/ast-graph", { code, language });
      const { nodes: serverNodes, edges: serverEdges } = res.data;
      
      // Super naive layout assignment for ReactFlow since we don't have dagre frontend-side easily without a package
      // We will just do a linear vertical layout
      const layoutedNodes = serverNodes.map((n, i) => ({
        ...n,
        position: { x: (i % 5) * 150, y: Math.floor(i / 5) * 100 },
        style: { 
            background: '#2a2a3c', 
            color: '#fff', 
            border: '1px solid #444', 
            borderRadius: '8px',
            padding: '10px',
            fontSize: '12px'
        }
      }));

      const formattedEdges = serverEdges.map(e => ({
        ...e,
        animated: true,
        style: { stroke: '#6366f1' },
      }));

      setNodes(layoutedNodes);
      setEdges(formattedEdges);
    } catch (err) {
      setError("Failed to fetch AST graph.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAST();
  }, [code, language]);

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  
  const onEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  if (loading) return <div className="p-4 text-gray-400">Loading AST...</div>;
  if (error) return <div className="p-4 text-red-400">{error}</div>;
  if (!nodes.length) return <div className="p-4 text-gray-500">No AST data available. Run analysis first.</div>;

  return (
    <div className="w-full h-[500px] border border-[#333] rounded-lg overflow-hidden bg-[#1e1e2d]">
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <Background color="#333" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
}

export default ASTGraph;
