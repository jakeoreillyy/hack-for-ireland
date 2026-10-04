"""Coordinate conversion between WGS84 (lat/lon in the API) and ITM (metres in the data)."""

from pyproj import Transformer

WGS84_TO_ITM = Transformer.from_crs("EPSG:4326", "EPSG:2157", always_xy=True)
ITM_TO_WGS84 = Transformer.from_crs("EPSG:2157", "EPSG:4326", always_xy=True)
