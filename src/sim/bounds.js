// Map extent and an inward safety margin are deliberately distinct concepts.
export const WORLD_BOUNDS=Object.freeze({minX:-6020,minZ:-6530,maxX:7300,maxZ:6280});
export const PLAY_BOUNDS=Object.freeze({minX:WORLD_BOUNDS.minX+50,minZ:WORLD_BOUNDS.minZ+50,maxX:WORLD_BOUNDS.maxX-50,maxZ:WORLD_BOUNDS.maxZ-50});
export const MAP_BOUNDS=Object.freeze({x:WORLD_BOUNDS.minX,z:WORLD_BOUNDS.minZ,w:WORLD_BOUNDS.maxX-WORLD_BOUNDS.minX,h:WORLD_BOUNDS.maxZ-WORLD_BOUNDS.minZ});
