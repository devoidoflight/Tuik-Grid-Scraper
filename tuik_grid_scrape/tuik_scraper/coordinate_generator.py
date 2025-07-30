import numpy as np
import json
from shapely.geometry import Polygon, Point

def load_geojson(filepath, il):
    """
    Opens up the source file and extracts the features for given district
    File source: https://github.com/izzetkalic/geojsons-of-turkey
    features: properties,id,name,geometry,geometry_type
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return [feature for feature in data["features"] if feature["properties"].get("name") == il] 

# Prepare polygons for systematic sampling
def extract_polygons(features):
    """
    Prepare polygons for systematic sampling
    """
    polygons = []
    for feature in features:
        geometry_type = feature["geometry"].get("type")  # Options: Polygon, MultiPolygon
        coordinates = feature["geometry"].get("coordinates")  # Polygon boundaries
        if geometry_type == "Polygon":
            if isinstance(coordinates, list) and len(coordinates) > 0:
                outer_ring = coordinates[0]  # The first element is the outer boundary
                polygons.append(Polygon(outer_ring))
        elif geometry_type == "MultiPolygon":
            for poly_coords in coordinates:
                if isinstance(poly_coords, list) and len(poly_coords) > 0:
                    outer_ring = poly_coords[0]  # The first element is the outer boundary
                    polygons.append(Polygon(outer_ring))
        else:
            raise ValueError(f"Unsupported geometry type: {geometry_type}")
    return polygons


def generate_grid(polygons, aralik):
    """
    This is not exactly a grid. We draw equally spaced lines on the polygon to divide it.
    Then we put dots on those lines where each of them are 100m's apart from each other.
    We use min-max lat-longs to determine our starting points.
    """
    red_points = [] # Points that are inside the polygons
    lat_spacing = aralik / 111320 # distance between two latitudes
    for polygon in polygons:
        min_lat = min(polygon.exterior.coords.xy[1]) 
        max_lat = max(polygon.exterior.coords.xy[1])
        lat_lines = np.arange(min_lat, max_lat, lat_spacing)
        for lat in lat_lines:
            min_lon = min(polygon.exterior.coords.xy[0]) 
            max_lon = max(polygon.exterior.coords.xy[0])
            lon_spacing = aralik / (111320 * np.cos(np.radians(lat)))
            lon_points = np.arange(min_lon, max_lon, lon_spacing)
            for lon in lon_points:
                point = Point(lon, lat)
                if any(polygon.contains(point) for polygon in polygons):
                    red_points.append((lon, lat))
    return red_points