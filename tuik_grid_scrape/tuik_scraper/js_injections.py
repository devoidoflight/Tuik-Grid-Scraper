MAP_HOOK = """
(() => {
  const OriginalMap = window.Map;
  window.Map = function (...args) {
    const instance = new OriginalMap(...args);
    setTimeout(() => {
      if (typeof instance.getZoom === 'function' && typeof instance.queryRenderedFeatures === 'function') {
        console.log('✅ Hooked map instance');
        window.__my_map = instance;
      }
    }, 1000);
    return instance;
  };
})();
"""

HOVER_LISTENER = """
window.__hoveredFeatures = [];

__my_map.on('mousemove', (e) => {
  const features = __my_map.queryRenderedFeatures(e.point, {
    layers: ['grid_katmani']
  });
  if (features.length > 0) {
    const f = features[0];
    const coords = f.geometry.coordinates;
    const props = f.properties;
    const id = props.gridid || JSON.stringify(coords);
    if (!window.__hoveredFeatures.find(entry => entry.id === id)) {
      window.__hoveredFeatures.push({
        id,
        timestamp: Date.now(),
        coordinates: coords,
        properties: props
      });
      console.log("🟢 Captured new square", id);
    }
  }
});
"""

CAPTURE_VISIBLE_GRID = """
window.__visibleGrids = [];

const allFeatures = window.__my_map.queryRenderedFeatures({ layers: ['grid_katmani'] });
const seenIds = new Set();

for (const f of allFeatures) {
  const props = f.properties;
  const id = props.gridid || JSON.stringify(f.geometry.coordinates);

  if (!seenIds.has(id)) {
    seenIds.add(id);
    window.__visibleGrids.push({
      id: id,
      timestamp: Date.now(),
      coordinates: f.geometry.coordinates,
      properties: props
    });
  }
}

console.log(`✅ Captured ${window.__visibleGrids.length} visible grid squares.`);
"""
