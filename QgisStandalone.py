from qgis.core import *
from PyQt5.QtCore import *
from qgis.gui import *
from qgis.core import *
from qgis.utils import *
# import os
# os.environ["PROJ_LIB"]="/Applications/QGIS-LTR.app/Contents/Resources/proj"

QgsApplication.setPrefixPath("/Applications/QGIS-LTR.app/Contents/MacOS", True)
qgs = QgsApplication([], False)
qgs.initQgis()



layerFields = QgsFields()
# layerFields.append(QgsField('ID', QVariant.Int))
# layerFields.append(QgsField('Value', QVariant.Double))
# layerFields.append(QgsField('Name', QVariant.String))

fn = '/Users/saimanojappalla/Desktop/PilotProject/KoboGeoserver/kobogeoserver-standalone/shapefile/new.shp'
writer = QgsVectorFileWriter(fn, 'UTF-8', layerFields, QgsWkbTypes.Point, QgsCoordinateReferenceSystem('EPSG:4326'), 'ESRI Shapefile')


# layer = QgsVectorLayer("/Users/saimanojappalla/Desktop/PilotProject/KoboGeoserver/kobogeoserver-standalone/shapefile/new.shp", "testlayer_shp", "ogr")
# print(layer)