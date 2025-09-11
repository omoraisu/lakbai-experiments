import osmnx as ox
import folium
from shapely.geometry import LineString
import geopandas as gpd

def generate_map(location="Mandaue City, Philippines", radius=500, filepath="maps/templates/maps/map.html"):
    # Configure OSMnx settings
    ox.settings.overpass_endpoint = "https://overpass.kumi.systems/api/interpreter"
    ox.settings.timeout = 180

    # Get center point
    center_point = ox.geocoder.geocode(location)

    # Get walking path
    streets = ox.graph_from_point(center_point, dist=radius, network_type='walk', simplify=False)

    # Project 
    streets = ox.project_graph(streets, to_crs='epsg:2154')

    # Convert to GeoDataFrames
    edges = ox.graph_to_gdfs(streets, nodes=False, edges=True)
    
    # Split edges into smaller segments 
    edges_split = split_edges_gdf(edges, n=5) 

    # Folium initialization
    center_lat, center_lon = center_point[0], center_point[1]
    m = folium.Map(location=[center_lat, center_lon], zoom_start=16)

    # Add edges to map with outline
    for _, row in edges_split.to_crs(epsg=4326).iterrows():
        geom = row.geometry.__geo_interface__
        seg_id = row['seg_id']

        gj = folium.GeoJson(
            geom,
            style_function=lambda x: {"color": "#FFDF22", "weight": 4, "opacity": 1.0},
            highlight_function=lambda x: {"weight": 6, "color": "red"},  # hover effect
        )

        # Popup with dummy annotation placeholder
        popup_html = f"""
                    <b>Segment ID:</b> {seg_id}<br>
                    <a href='#' onclick="alert('Annotation form for segment {seg_id} will go here!')">
                        Annotate this segment
                    </a>
                    """

        # Outer stroke
        folium.GeoJson(
            geom,
            style_function=lambda x: {"color": "black", "weight": 9, "opacity": 1.0},
        ).add_to(m)

        # Inner stroke
        folium.GeoJson(
            geom,
            style_function=lambda x: {"color": "#FFDF22", "weight": 4, "opacity": 1.0},
        ).add_to(m)

        folium.Popup(popup_html, max_width=250).add_to(gj)
        gj.add_to(m)

    m.save("maps/templates/maps/old_map.html")

def get_edges_gdf(location="Mandaue City, Philippines", radius=500, n=5):
    # OSMnx config
    ox.settings.overpass_endpoint = "https://overpass.kumi.systems/api/interpreter"
    ox.settings.timeout = 180

    # Get center point
    center_point = ox.geocoder.geocode(location)

    # Build walking graph
    streets = ox.graph_from_point(center_point, dist=radius, network_type='walk', simplify=False)
    streets = ox.project_graph(streets, to_crs='epsg:2154')

    # Edges GeoDataFrame
    edges = ox.graph_to_gdfs(streets, nodes=False, edges=True)

    # Split edges into n parts
    edges_split = split_edges_gdf(edges, n=n)

    # Reproject to WGS84 for Leaflet
    return edges_split.to_crs(epsg=4326)

# Split line segment into equal parts 
def split_line_equal(line: LineString, n: int):
    if not isinstance(line, LineString):
        raise ValueError("Input must be a LineString")
    total_length = line.length
    segment_length = total_length / n

    points = [line.interpolate(i * segment_length) for i in range(n + 1)]
    segments = [LineString([points[i], points[i + 1]]) for i in range(n)]
    return segments

# Apply to OSM street edge 
def split_edges_gdf(edges: gpd.GeoDataFrame, n: int):
    new_edges = []
    seg_id = 0
    for idx, row in edges.iterrows():
        line = row.geometry
        try:
            segments = split_line_equal(line, n)
            for seg in segments:
                new_row = row.copy()
                new_row.geometry = seg
                new_row['seg_id'] = seg_id
                seg_id += 1
                new_edges.append(new_row)
        except ValueError:
            continue
    
    gdf = gpd.GeoDataFrame(new_edges)
    gdf.set_crs(edges.crs, inplace=True)
    return gdf