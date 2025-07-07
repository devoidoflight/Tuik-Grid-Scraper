1. We go to sources-> static->js->main.8da9294f.chunk.js and search for queryRenderedFeatures
2.  We find var t = i.map.queryRenderedFeatures(e.point, {
                                layers: ["grid_katmani"] 
line and add breakpoint to it manually. Then hover on the grid to make it stop
3. run window.__my_map = i.map; on console 
4. run __my_map.getZoom() to see if that workedç    