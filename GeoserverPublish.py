from Geoserver import Geoserver
import configparser

config = configparser.ConfigParser()
config.read('GeoserverAuth.ini')

# url = config['Geoserver Credentials']['Url']
# username = config['Geoserver Credentials']['Username']
# password = config['Geoserver Credentials']['password']
# shp_workspace_name = config['Shapefile Workspace Store']['workspace_name']
# shp_store_name = config['Shapefile Workspace Store']['store_name']
# shp_path = config['Shapefile Workspace Store']['shp_path']
# layer_name = shp_path.split('/')[-1].split('.')[0]

geo = Geoserver("http://localhost:8080/geoserver", username="admin", password="geoserver")
geo.create_workspace(workspace='testpgpublishworkspace')
# geo.delete_layer(layer_name, shp_workspace_name)
geo.create_featurestore(store_name='testpgpublishstore', workspace='testpgpublishworkspace', db='saimanojappalla', host='localhost', pg_user='postgres',
                        pg_password='postgres')
geo.publish_featurestore(workspace='testpgpublishworkspace', store_name='testpgpublishstore', pg_table='wards')


# geo.publish_featurestore(workspace=shp_workspace_name, store_name=shp_store_name,pg_table=layer_name)