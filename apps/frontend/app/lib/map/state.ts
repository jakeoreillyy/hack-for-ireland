import { useState } from '#imports'

/** Map UI state shared by the shell, the map and the map controls. */
export function useMapUi() {
  return {
    /** null = use the device default (3D on desktop, 2D on mobile). */
    is3D: useState<boolean | null>('map:3d', () => null),
    /** Bumped by the recentre control. */
    recentre: useState<number>('map:recentre', () => 0),
    /** Zoom button requests; `n` makes repeats observable. */
    zoomBy: useState<{ delta: number; n: number } | null>('map:zoom', () => null),
  }
}
