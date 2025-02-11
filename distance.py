
import pyproj
from pyproj import Proj, transform
import pandas as pd
import json
import sys
import math
import folium
from folium.plugins import MeasureControl
from selenium import webdriver
import time
import re
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.geometry import Polygon, Point
from shapely.ops import nearest_points
from geopy.distance import geodesic


# Define UTM projection for Zone 43N
utm_proj = Proj(proj="utm", zone=43, datum="WGS84", south=False)
wgs84_proj = Proj(proj="latlong", datum="WGS84")

# Function to convert decimal degrees to DMS
def decimal_to_dms(decimal_degree):
    degrees = int(decimal_degree)
    minutes = int((abs(decimal_degree) - abs(degrees)) * 60)
    seconds = (abs(decimal_degree) - abs(degrees) - minutes / 60) * 3600
    return degrees, minutes, seconds

# Function to calculate distance using the Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of Earth in kilometers
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c



def map_sattelite(coords, points_with_labels,nearest_points_list, output_map="map.html"):
    """
    Create a folium map with a polygon, labeled points, and an export-to-PDF button on Google Satellite imagery.
    
    Args:
        coords (list): List of (latitude, longitude) tuples for the polygon.
        points_with_labels (list): List of tuples [(lat, lon, label), ...] for points with labels.
        output_map (str): Path to save the output HTML map.
    
    Returns:
        str: Path to the saved HTML map.
    """
   
    m = folium.Map(
        location=[coords[0][0], coords[0][1]],
        zoom_start=10,
        tiles=None  # Disable default tiles
    )
    m.add_child(MeasureControl())

    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="OpenStreetMap",
        name="OpenStreetMap",
        overlay=False,
        control=True  # Allow users to toggle this layer
    ).add_to(m)
    
    # Add Google Satellite Tiles
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google Satellite",
        name="Google Satellite",
        overlay=False,
        control=True
    ).add_to(m) 
    
    polygon = folium.Polygon(
        locations=coords,  # List of (latitude, longitude) tuples
        color="red",
        weight=3,
        fill=True,
        fill_color="cyan",
        fill_opacity=0.4,
        popup="Polygon Area"
    ).add_to(m)

    Aviation_boundary = folium.WmsTileLayer(
        url="https://iwmsgis.pmc.gov.in/geoserver/wms?",
        name="Aviation Boundaries",
        layers="MOD:Aviation_Boundary",
        fmt="image/png",
        transparent=True,
        overlay=True,
        control=True
    ).add_to(m)

    
    Aviation_zone =folium.WmsTileLayer(
        url="https://iwmsgis.pmc.gov.in/geoserver/wms?",
        name="Aviation Zone",
        layers="MOD:Aviation_data",
        fmt="image/png",
        transparent=True,
        overlay=True,
        control=True
    ).add_to(m)

   
    for point_pair in nearest_points_list:
    # Each point_pair is a tuple of two points
        point1 = point_pair[0]  
        point2 = point_pair[1] 

        # Calculate the distance between the two points using geodesic (this calculates the great-circle distance)
        line_length = geodesic(point1, point2).kilometers  # Distance in kilometers

        mid_point_lat = (point1[0] + point2[0]) / 2
        mid_point_lon = (point1[1] + point2[1]) / 2
        popup_message = f"Distance: {line_length:.2f} km"  # Format the distance to two decimal places

        # Add the PolyLine to the map with the popup showing the distance
        folium.PolyLine(
            locations=[point1, point2],  # Coordinates of the points to draw a line between
            color="yellow",  # Color for the line
            weight=1,  # Line thickness
        ).add_to(m).add_child(folium.Popup(popup_message))

        folium.Marker(
        location=[mid_point_lat, mid_point_lon],  # Midpoint of the line
        icon=folium.DivIcon(
            icon_size=(150, 36),  # Size of the label
            icon_anchor=(7, 20),  # Position of the label
            html=f'<div style="font-size: 16px; font-weight: bold; color: yellow;">{line_length:.2f} km</div>'  # Label style
        ),
    ).add_to(m)


    for lat, lon, label in points_with_labels:
        folium.CircleMarker(
            location=(lat, lon),
            radius=3,  # Small dot size
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.5,
            popup=f"{label}",  # Add label as a popup
        ).add_to(m)

        folium.Marker(
        location=[lat, lon], 
        icon=folium.DivIcon(
            icon_size=(150, 36),  # Size of the label
            icon_anchor=(7, 20),  # Position of the label
            html=f'<div style="font-size: 12px; font-weight: bold; color: yellow;">{label}</div>'  # Label style
        ),
    ).add_to(m)

    m.fit_bounds(polygon.get_bounds()) 
    # Add a custom button to export to PDF
    pdf_button = """
      <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js" integrity="sha512-BNaRQnYJYiPSqHHDb58B0yaPfCu+Wgds8Gp/gU33kqBtgNS4tSPHuGibyoeqMV/TJlSKda6FXzoEyYGjTe+vXA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 150px; height: 30px; 
                            z-index: 1000;">
                    <button onclick="exportToPDF()" style="width: 150px; height: 30px; background-color: #4CAF50; color: white; border: none; border-radius: 5px;">
                        Export to PDF
                    </button>
                </div>
            
                <script>
                function exportToPDF() {
    try {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // Select the map container dynamically
        const mapContainer = document.querySelector('.folium-map');

        const originalScrollX = window.scrollX;
        const originalScrollY = window.scrollY;

        html2canvas(mapContainer, {
            scale: 2, // Scale for high resolution
            useCORS: true, // Handle cross-origin images
            scrollX: originalScrollX, // Maintain original horizontal scroll position
            scrollY: originalScrollY, // Maintain original vertical scroll position
        }).then(function (canvas) {
            const imgData = canvas.toDataURL('image/png');
            const pdfWidth = 180; // Maximum width for PDF
            const aspectRatio = canvas.width / canvas.height;
            const imgHeight = pdfWidth / aspectRatio; // Maintain aspect ratio

            // Center the map image in the PDF
            const pageWidth = doc.internal.pageSize.getWidth();
            const centerX = (pageWidth - pdfWidth) / 2;

            // Add the image to the PDF
            doc.addImage(imgData, 'PNG', centerX, 10, pdfWidth, imgHeight);

            // Save the generated PDF
            const fileName = `map_export.pdf`;
            doc.save(fileName);
        });
    } catch (error) {
        console.error('Error generating PDF:', error);
        alert('Failed to generate PDF. Check console for details.');
    }
}


    </script>
    """
    m.get_root().html.add_child(folium.Element(pdf_button))

    folium.LayerControl().add_to(m)
    m.save(output_map)
    return output_map

def convert_to_wgs84(x, y):
    lon, lat = transform(utm_proj, wgs84_proj, x, y)
    return lat, lon


def calculate_boundaryDistance(coords):

    wmsUrlNDALohgaonBOundary = "http://iwmsgis.pmc.gov.in/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=MOD:Aviation_Boundary&outputFormat=application/json"
    geoserver_layer = gpd.read_file(wmsUrlNDALohgaonBOundary)
    geoserver_layer = geoserver_layer.to_crs(epsg=32643) 
    polygon_nda = geoserver_layer[geoserver_layer["Aviation_N"] == "NDA"]
    polygon_lohgaon = geoserver_layer[geoserver_layer["Aviation_N"] == "Lohagaon"]
    

    # Create polygon from input coordinates
    polygon_layout = gpd.GeoDataFrame(
        {'geometry': [Polygon(coords)]},
        crs="EPSG:32643"  # Original CRS for input coordinates (WGS84)
    ).geometry.iloc[0]
   
    polygon_nda = polygon_nda.to_crs(epsg=32643).geometry.iloc[0]
    polygon_lohgaon = polygon_lohgaon.to_crs(epsg=32643).geometry.iloc[0]

    # calculate nearest point
    nearest_nda_point = nearest_points(polygon_layout, polygon_nda)[1]
    nearest_lohgaon_point = nearest_points(polygon_layout, polygon_lohgaon)[1]
    polygon_layout_NDA = nearest_points(polygon_nda,polygon_layout)[1]
    polygon_layout_Lohagaon = nearest_points(polygon_lohgaon,polygon_layout)[1]

    nearest_nda_point_wgs84 = convert_to_wgs84(nearest_nda_point.x, nearest_nda_point.y)
    nearest_lohgaon_point_wgs84 = convert_to_wgs84(nearest_lohgaon_point.x, nearest_lohgaon_point.y)
    nearest_polygon_layout_NDA_wgs84 = convert_to_wgs84(polygon_layout_NDA.x,polygon_layout_NDA.y)
    nearest_polygon_layout_Lohagaon_wgs84 = convert_to_wgs84(polygon_layout_Lohagaon.x,polygon_layout_Lohagaon.y)

     # calculate distance point
    distance_meters_nda = polygon_nda.distance(polygon_layout)
    distance_meters_lohgaon = polygon_lohgaon.distance(polygon_layout)
    distance_km_nda = distance_meters_nda / 1000
    distance_km_lohgaon = distance_meters_lohgaon / 1000
    
    # Return the distances in a dictionary
    mindistance = {
        "NDAboundaryMinDistance": distance_km_nda,
        "LohgaonBoundaryMinDistance": distance_km_lohgaon
    }
    nearest_points_list = [
        [nearest_nda_point_wgs84, nearest_polygon_layout_NDA_wgs84],  # (lat, lon) format for folium
        [nearest_lohgaon_point_wgs84, nearest_polygon_layout_Lohagaon_wgs84]
    ] 
    return mindistance,nearest_points_list


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Please provide a CSV file path as input"}))
        sys.exit(1)

    try:
        csv_path = sys.argv[1]

        data = pd.read_csv(csv_path)
        # print(data)
        if data.shape[1] < 4:
            print(json.dumps({"error": "CSV file must contain at least 3 columns (P name, UTM x, UTM y, Height)"}))
            sys.exit(1)

        p_names = data.iloc[:, 0]
        utm_x = data.iloc[:, 1]
        utm_y = data.iloc[:, 2]
        Height = data.iloc[:, 3]
        decimal_degrees = []
        fpoints = []
        utmpoints =[] 
        fpointswithlabel =[]
        reference_points = {
            "NDA": {"utm_x": 371129.923, "utm_y": 2042927.865},
            "loh": {"utm_x": 385999.526, "utm_y": 2055079.640},
        }

        for ref_name, ref_coords in reference_points.items():
            lon, lat = transform(utm_proj, wgs84_proj, ref_coords["utm_x"], ref_coords["utm_y"])
            reference_points[ref_name]["latitude"] = lat
            reference_points[ref_name]["longitude"] = lon

        for p_name, x, y, z in zip(p_names, utm_x, utm_y,Height):
            lon, lat = transform(utm_proj, wgs84_proj, x, y)
            lat_dms = decimal_to_dms(lat)
            lon_dms = decimal_to_dms(lon)
            utmpoint = (x,y)
            Heights = z
            utmpoints.append(utmpoint)
            distances = {}
            for ref_name, ref_coords in reference_points.items():
                distances[ref_name] = haversine(lat, lon, ref_coords["latitude"], ref_coords["longitude"])

            if isinstance(p_name, str) and re.match(r"^\s*[Pp]", p_name):
                points = (lat,lon)
                pointslabel =(lat,lon,p_name)
                fpoints.append(points)
                fpointswithlabel.append(pointslabel)

            decimal_degrees.append({
                "P_name": p_name,
                "latitude": lat,
                "longitude": lon,
                "Height":Heights,
                "latitude_dms": f"{lat_dms[0]}°{lat_dms[1]}'{lat_dms[2]:.4f}\"",
                "longitude_dms": f"{lon_dms[0]}°{lon_dms[1]}'{lon_dms[2]:.4f}\"",
                "distances_to_reference_points_km": distances
            })

        boundary_distances, nearest_points_list = calculate_boundaryDistance(utmpoints)
        map_sattelite(fpoints,fpointswithlabel,nearest_points_list) 

        result = {
            "decimal_degrees": decimal_degrees,
            "boundary_distances":boundary_distances,
        }

        print(json.dumps(result, indent=4))

    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
