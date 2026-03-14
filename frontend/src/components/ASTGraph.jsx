import React, { useEffect, useState, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import ReactFlow, { 
  Background, 
  Controls, 
  applyNodeChanges, 
  applyEdgeChanges,
  MarkerType 
} from 'reactflow';
import 'reactflow/dist/style.css';
import api from '../api';
import dagre from 'dagre';
import { Maximize, Minimize } from 'lucide-react';

const nodeTypes = {}; 

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  // Add nodes to dagre
  nodes.forEach((node) => {
    // Estimating node dimensions width: 150, height: 50
    dagreGraph.setNode(node.id, { width: 200, height: 60 });
  });

  // Add edges to dagre
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Auto-calculate
  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    // Shift slightly to center
    node.targetPosition = isHorizontal ? 'left' : 'top';
    node.sourcePosition = isHorizontal ? 'right' : 'bottom';
    
    node.position = {
      x: nodeWithPosition.x - 100, // half of width
      y: nodeWithPosition.y - 30,  // half of height
    };

    return node;
  });

  return { nodes: layoutedNodes, edges };
};

function ASTGraph({ code, language }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const graphContainerRef = useRef(null);

  const fetchAST = async () => {
    if (!code) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.post("/ast-graph", { code, language });
      const { nodes: serverNodes, edges: serverEdges } = res.data;
      
      const styledNodes = serverNodes.map((n) => ({
        ...n,
        style: { 
            background: '#2a2a3c', 
            color: '#fff', 
            border: '1px solid #444', 
            borderRadius: '8px',
            padding: '10px',
            fontSize: '12px',
            width: 200,
            textAlign: 'center'
        }
      }));

      const formattedEdges = serverEdges.map(e => ({
        ...e,
        animated: true,
        style: { stroke: '#6366f1' },
      }));

      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        styledNodes,
        formattedEdges,
        'TB' // Top-to-Bottom
      );

      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
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

  // Handle ESC key for exiting fullscreen
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
      }
    };
    if (isFullscreen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen]);

  const toggleFullscreen = () => setIsFullscreen(!isFullscreen);

  if (loading) return <div className="p-4 text-gray-400">Loading AST...</div>;
  if (error) return <div className="p-4 text-red-400">{error}</div>;
  if (!nodes.length) return <div className="p-4 text-gray-500">No AST data available. Run analysis first.</div>;

  const graphContent = (
    <div 
      ref={graphContainerRef}
      className={`relative w-full border border-[#333] overflow-hidden bg-[#1e1e2d] transition-all duration-300 ${
        isFullscreen 
          ? 'h-full w-full rounded-xl shadow-2xl border border-[#444]' 
          : 'h-[500px] rounded-lg'
      }`}
    >
      <button
        onClick={toggleFullscreen}
        className="absolute top-4 right-4 z-[110] p-2 bg-[#2a2a3c] hover:bg-[#3a3a4c] text-white rounded-md border border-[#444] shadow-lg transition-colors flex items-center gap-2 group"
        title={isFullscreen ? "Minimize (Esc)" : "Fullscreen"}
      >
        {isFullscreen ? <Minimize size={18} /> : <Maximize size={18} />}
        <span className="text-xs font-medium hidden group-hover:block whitespace-nowrap">
          {isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
        </span>
      </button>

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

  if (isFullscreen) {
    return (
      <>
        <div className="h-[500px] w-full border border-dashed border-[#444] rounded-lg bg-[#1e1e2d] opacity-50 flex items-center justify-center text-gray-400">
          AST is in fullscreen mode
        </div>
        {createPortal(
          <div className="fixed inset-0 z-[9999] bg-black/70 backdrop-blur-sm flex items-center justify-center p-8">
            <div className="w-full h-full max-w-[95vw] max-h-[95vh] relative animate-in fade-in zoom-in-95 duration-200">
              {graphContent}
            </div>
          </div>,
          document.body
        )}
      </>
    );
  }

  return graphContent;
}

export default ASTGraph;
