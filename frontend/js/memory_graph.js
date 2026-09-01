// Interactive Force-Directed Knowledge Graph Visualizer on HTML5 Canvas

class MemoryGraphVisualizer {
  constructor(canvasId, infoPanelId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.infoPanel = document.getElementById(infoPanelId);

    this.nodes = [];
    this.edges = [];
    this.stats = {};

    this.width = this.canvas.clientWidth;
    this.height = this.canvas.clientHeight;

    this.transform = { x: 0, y: 0, scale: 1 };
    this.isDragging = false;
    this.draggedNode = null;
    this.dragStart = { x: 0, y: 0 };
    this.selectedNode = null;
    this.animationId = null;

    this.categoryColors = {
      'user': '#ffffff',
      'identity': '#38bdf8',
      'preference': '#c084fc',
      'project': '#34d399',
      'skill': '#fbbf24',
      'skill_tracker': '#f59e0b',
      'concept': '#22d3ee',
      'knowledge_note': '#a78bfa'
    };

    this.initEvents();
  }

  initEvents() {
    window.addEventListener('resize', () => this.resize());
    this.resize();

    // Mouse & Touch interactions
    this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
    this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
    window.addEventListener('mouseup', () => this.onMouseUp());
    this.canvas.addEventListener('wheel', (e) => this.onWheel(e), { passive: false });
  }

  resize() {
    if (!this.canvas) return;
    this.width = this.canvas.parentElement.clientWidth;
    this.height = Math.max(500, this.canvas.parentElement.clientHeight || 550);
    this.canvas.width = this.width * window.devicePixelRatio;
    this.canvas.height = this.height * window.devicePixelRatio;
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;
    this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }

  async loadData() {
    try {
      const data = await api.getKnowledgeGraph();
      this.stats = data.stats;
      this.processData(data.nodes, data.edges);
      this.startSimulation();
    } catch (err) {
      console.error('Failed to load knowledge graph:', err);
    }
  }

  processData(nodes, edges) {
    const cx = this.width / 2;
    const cy = this.height / 2;

    this.nodes = nodes.map((n, idx) => {
      // Retain previous positions if re-rendering
      const existing = this.nodes.find(old => old.id === n.id);
      const angle = (idx / nodes.length) * Math.PI * 2;
      const radius = n.id === 'node_user' ? 0 : 120 + Math.random() * 150;

      return {
        ...n,
        x: existing ? existing.x : cx + Math.cos(angle) * radius,
        y: existing ? existing.y : cy + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        radius: n.id === 'node_user' ? 24 : 12 + Math.min(10, (n.importance || 1) * 5),
        color: this.categoryColors[n.category] || '#94a3b8'
      };
    });

    const nodeMap = new Map(this.nodes.map(n => [n.id, n]));
    this.edges = edges.map(e => ({
      ...e,
      sourceNode: nodeMap.get(e.source),
      targetNode: nodeMap.get(e.target)
    })).filter(e => e.sourceNode && e.targetNode);
  }

  startSimulation() {
    if (this.animationId) cancelAnimationFrame(this.animationId);

    const simulate = () => {
      this.tick();
      this.render();
      this.animationId = requestAnimationFrame(simulate);
    };
    simulate();
  }

  tick() {
    const cx = this.width / 2;
    const cy = this.height / 2;

    // 1. Repulsion between nodes
    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const n1 = this.nodes[i];
        const n2 = this.nodes[j];
        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const minDist = n1.radius + n2.radius + 40;

        if (dist < 320) {
          const force = (320 - dist) / dist * 0.05;
          n1.vx -= dx * force;
          n1.vy -= dy * force;
          n2.vx += dx * force;
          n2.vy += dy * force;
        }
      }
    }

    // 2. Spring attraction along edges
    for (const e of this.edges) {
      const dx = e.targetNode.x - e.sourceNode.x;
      const dy = e.targetNode.y - e.sourceNode.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const targetDist = 110;
      const force = (dist - targetDist) * 0.008 * (e.weight || 1);

      e.sourceNode.vx += (dx / dist) * force;
      e.sourceNode.vy += (dy / dist) * force;
      e.targetNode.vx -= (dx / dist) * force;
      e.targetNode.vy -= (dy / dist) * force;
    }

    // 3. Center gravity & damping
    for (const n of this.nodes) {
      if (n === this.draggedNode) continue;
      
      const dx = cx - n.x;
      const dy = cy - n.y;
      n.vx += dx * 0.001;
      n.vy += dy * 0.001;

      n.vx *= 0.88;
      n.vy *= 0.88;

      n.x += n.vx;
      n.y += n.vy;
    }
  }

  render() {
    this.ctx.save();
    this.ctx.clearRect(0, 0, this.width, this.height);

    // Apply viewport transform (pan & zoom)
    this.ctx.translate(this.transform.x, this.transform.y);
    this.ctx.scale(this.transform.scale, this.transform.scale);

    // Draw Edges
    for (const e of this.edges) {
      this.ctx.beginPath();
      this.ctx.moveTo(e.sourceNode.x, e.sourceNode.y);
      this.ctx.lineTo(e.targetNode.x, e.targetNode.y);
      this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
      this.ctx.lineWidth = Math.min(2.5, 0.8 * (e.weight || 1));
      this.ctx.stroke();
    }

    // Draw Nodes
    const time = Date.now() * 0.002;
    for (const n of this.nodes) {
      const isSelected = this.selectedNode && this.selectedNode.id === n.id;
      const isUser = n.id === 'node_user';

      // Glow effect for selected or anchor node
      if (isSelected || isUser || n.is_pinned) {
        this.ctx.save();
        this.ctx.shadowColor = n.color;
        this.ctx.shadowBlur = isSelected ? 22 : (isUser ? 28 : 12);
        this.ctx.beginPath();
        this.ctx.arc(n.x, n.y, n.radius + 3, 0, Math.PI * 2);
        this.ctx.fillStyle = n.color + '44';
        this.ctx.fill();
        this.ctx.restore();
      }

      // Main node body
      this.ctx.beginPath();
      this.ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      this.ctx.fillStyle = isUser ? '#ffffff' : n.color;
      this.ctx.fill();

      // Border
      this.ctx.strokeStyle = isSelected ? '#ffffff' : 'rgba(15, 23, 42, 0.8)';
      this.ctx.lineWidth = 2;
      this.ctx.stroke();

      // Label
      this.ctx.font = isUser ? 'bold 13px "Plus Jakarta Sans"' : '500 11px "Plus Jakarta Sans"';
      this.ctx.fillStyle = isSelected ? '#ffffff' : '#cbd5e1';
      this.ctx.textAlign = 'center';
      this.ctx.fillText(n.label, n.x, n.y + n.radius + 14);
    }

    this.ctx.restore();
  }

  // Coordinate Conversion
  getMousePos(e) {
    const rect = this.canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;
    return {
      x: (clientX - this.transform.x) / this.transform.scale,
      y: (clientY - this.transform.y) / this.transform.scale,
      rawX: clientX,
      rawY: clientY
    };
  }

  getNodeAt(pos) {
    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const n = this.nodes[i];
      const dx = pos.x - n.x;
      const dy = pos.y - n.y;
      if (Math.sqrt(dx * dx + dy * dy) <= n.radius + 6) {
        return n;
      }
    }
    return null;
  }

  onMouseDown(e) {
    const pos = this.getMousePos(e);
    const node = this.getNodeAt(pos);

    if (node) {
      this.draggedNode = node;
      this.selectedNode = node;
      this.showNodeDetails(node);
    } else {
      this.isDragging = true;
      this.dragStart = { x: e.clientX - this.transform.x, y: e.clientY - this.transform.y };
      this.selectedNode = null;
      this.hideNodeDetails();
    }
  }

  onMouseMove(e) {
    const pos = this.getMousePos(e);
    if (this.draggedNode) {
      this.draggedNode.x = pos.x;
      this.draggedNode.y = pos.y;
      this.draggedNode.vx = 0;
      this.draggedNode.vy = 0;
    } else if (this.isDragging) {
      this.transform.x = e.clientX - this.dragStart.x;
      this.transform.y = e.clientY - this.dragStart.y;
    } else {
      const hoverNode = this.getNodeAt(pos);
      this.canvas.style.cursor = hoverNode ? 'pointer' : 'grab';
    }
  }

  onMouseUp() {
    this.isDragging = false;
    this.draggedNode = null;
    this.canvas.style.cursor = 'default';
  }

  onWheel(e) {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    const newScale = Math.min(2.5, Math.max(0.4, this.transform.scale * zoomFactor));
    
    const rect = this.canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    this.transform.x = mouseX - (mouseX - this.transform.x) * (newScale / this.transform.scale);
    this.transform.y = mouseY - (mouseY - this.transform.y) * (newScale / this.transform.scale);
    this.transform.scale = newScale;
  }

  showNodeDetails(node) {
    if (!this.infoPanel) return;
    const badgeClass = `badge-${node.category}`;
    this.infoPanel.innerHTML = `
      <div class="p-4 rounded-xl glass-panel border border-slate-700/60 animate-fadeIn">
        <div class="flex items-center justify-between gap-2 mb-2">
          <h4 class="font-bold text-slate-100 text-sm flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full" style="background-color: ${node.color};"></span>
            ${node.label}
          </h4>
          <span class="px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${badgeClass}">${node.category}</span>
        </div>
        <p class="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">${node.details}</p>
        <div class="mt-3 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-700/40 pt-2">
          <span>Importance: ${Number(node.importance || 1).toFixed(1)}x</span>
          <span>${node.is_pinned ? '📌 Pinned Priority' : 'Auto-Learned'}</span>
        </div>
      </div>
    `;
    this.infoPanel.classList.remove('hidden');
  }

  hideNodeDetails() {
    if (this.infoPanel) {
      this.infoPanel.innerHTML = `
        <div class="p-4 rounded-xl glass-panel border border-slate-800 text-center text-xs text-slate-500">
          <p>Click any node in the knowledge network to inspect its learned details and connections.</p>
        </div>
      `;
    }
  }

  resetView() {
    this.transform = { x: 0, y: 0, scale: 1 };
  }
}
