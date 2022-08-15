from Geoserver import Geoserver
import configparser

config = configparser.ConfigParser()
config.read('GeoserverAuth.ini')

url = config['Geoserver Credentials']['Url']
username = config['Geoserver Credentials']['Username']
password = config['Geoserver Credentials']['password']
shp_workspace_name = config['Shapefile Workspace Store']['workspace_name']
shp_store_name = config['Shapefile Workspace Store']['store_name']
shp_path = config['Shapefile Workspace Store']['shp_path']
layer_name = shp_path.split('/')[-1].split('.')[0]

geo = Geoserver(url, username=username, password=password)

geo.delete_layer(layer_name, shp_workspace_name)
geo.create_datastore(name=shp_store_name, path=shp_path,workspace=shp_workspace_name)

# geo.publish_featurestore(workspace=shp_workspace_name, store_name=shp_store_name,pg_table=layer_name)