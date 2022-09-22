# Import all the libraries
from time import sleep
from datetime import datetime
from qgis import processing

# Initialize all the variables
canvas = iface.mapCanvas()
previous_count = 0
new_count = 0

for i in range(24):
    
    # Get the current time
    now = datetime.now()
    
    # Open the active layer
    QgsProject.instance().removeMapLayer(iface.activeLayer())
    url = "http://localhost:8080/geoserver/KoboGeoserverPgWorkspace/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=KoboGeoserverPgWorkspace:pg_soil_temp_kobo"
    vlayer = QgsVectorLayer(url, "test", "WFS")
    
    # Count no of featueres in the layer
    new_count = vlayer.featureCount()
    print(new_count)
    
    # Check if the layer is valid or not
    if vlayer.isValid():
        print("valid")
    name = vlayer.name()
    
    # Add the layer to map
    QgsProject.instance().addMapLayer(vlayer)
    
    if new_count > previous_count:
        # URL of the output directory
        output = '/Users/saimanojappalla/Desktop/add/interpolation/image_{}.tiff'.format(now.strftime("%H:%M:%S"))
        
        # Algorithm Parameters
        alg_params = {
                'DISTANCE_COEFFICIENT': 2,
                'EXTENT': iface.activeLayer().extent(),
                'INTERPOLATION_DATA': 'http://localhost:8080/geoserver/KoboGeoserverPgWorkspace/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=KoboGeoserverPgWorkspace:pg_soil_temp_kobo::~::0::~::0::~::0',
                'COLUMNS':234,
                'ROWS':100,
                'OUTPUT': output
            }
        processing.run('qgis:idwinterpolation', alg_params)
    
    previous_count = new_count
    # Sleep happily for 10sec
    sleep(10)
    
    