# IMPORT ALL THE NECESSARY LIBRARIES
import os
import requests
import configparser
import xml.etree.ElementTree as ET
from qgis.core import *
from qgis.utils import *
import json
from PyQt5.QtCore import *
from Auth import Auth
from Geoserver import Geoserver

"""
********************************* SETUPT ALL THE VARIABLES - START *****************************************************
"""
# GEOSERVER VARIABLES
config = configparser.ConfigParser()
config.read('GeoserverAuth.ini')

url_geoserver = config['Geoserver Credentials']['Url']
username_geoserver = config['Geoserver Credentials']['Username']
password_geoserver = config['Geoserver Credentials']['password']

# ODK VARIABLES
odk = configparser.ConfigParser()
odk.read('OdkAuth.ini')

url_odk = odk['Odk Credentials']['url']
username_odk = odk['Odk Credentials']['username']
password_odk = odk['Odk Credentials']['password']
last_submission_odk = odk['Odk Credentials']['last submission']
form_feature_count_odk = 0
last_project_used_odk = odk['Odk Credentials']['last used project']
last_form_used_odk = odk[last_project_used_odk]['last selected form']
last_selected_form_id = odk[last_project_used_odk][last_form_used_odk]

# ODK-GEOSERVER VARIABLES
shp_workspace_name_odk = config['Shapefile Workspace Store']['workspace_name_odk']
shp_store_name_odk = config['Shapefile Workspace Store']['store_name_odk']
shp_path_odk = config['Shapefile Workspace Store']['shp_path_odk']
no_of_times_published_odk = int(config['Shapefile Workspace Store']['publish_count_odk'])

"""
************************************************************************************************************************
"""


# INITIALIZE STANDALONE APPLICATION
QgsApplication.setPrefixPath("/Applications/QGIS-LTR.app/Contents/Resources", True)
qgs = QgsApplication([], False)
qgs.initQgis()


# START WRITING THE FUNCTIONS
def qtype(odktype):
    if odktype == 'binary':
        return QVariant.String,{'DocumentViewer': 2, 'DocumentViewerHeight': 0, 'DocumentViewerWidth': 0, 'FileWidget': True, 'FileWidgetButton': True, 'FileWidgetFilter': '', 'PropertyCollection': {'name': None, 'properties': {}, 'type': 'collection'}, 'RelativeStorage': 0, 'StorageMode': 0}
    elif odktype=='string':
        return QVariant.String,{}
    elif odktype[:3] == 'sel' :
        return QVariant.String,{}
    elif odktype[:3] == 'int':
        return QVariant.Int, {}
    elif odktype[:3]=='dat':
        return QVariant.Date, {}
    elif odktype[:3]=='ima':
        return QVariant.String,{'DocumentViewer': 2, 'DocumentViewerHeight': 0, 'DocumentViewerWidth': 0, 'FileWidget': True, 'FileWidgetButton': True, 'FileWidgetFilter': '', 'PropertyCollection': {'name': None, 'properties': {}, 'type': 'collection'}, 'RelativeStorage': 0, 'StorageMode': 0}
    elif odktype == 'Hidden':
        return 'Hidden'
    else:
        return (QVariant.String),{}


# CREATE CLASS
class ImportOdk():

    def __init__(self):
        # user auth token
        self.usertoken = ""
        # corresponding id for entered project name
        self.project_id = 0
        # name of selected form
        self.form_name = ""
        self.tag = "ODK Central"

    def getFormList(self):
        """Retrieves list of all forms using user entered credentials
        Returns
        ------
        forms - dictionary
            contains all forms in user's account
        x - HTTP response
            authentication response
        """

        user = username_odk
        password = password_odk
        c_url = url_odk
        data = {'email': user, 'password': password}
        if not c_url:
            print("Enter url in OdkAuth.ini file")
            return None, None
        headers = {"Content-Type": "application/json"}
        projects = {}
        forms = {}
        project_name = last_project_used_odk
        try:
            x = requests.post(c_url + "v1/sessions", json=data, headers=headers)
            token = x.json()["token"]
            self.usertoken = token
            projects_response = requests.get(c_url + "v1/projects/", headers={"Authorization": "Bearer " + token})
            for p in projects_response.json():
                if p["name"] == project_name:
                    self.project_id = p["id"]
            form_response = requests.get(c_url + "v1/projects/" + str(self.project_id) + "/forms/",
                                         headers={"Authorization": "Bearer " + token})
            for form in form_response.json():
                forms[form["name"]] = form["enketoOnceId"]
            return forms, x
        except:
            print("Invalid url, username, project name or password")
            return None, None

    def flattenValues(self, nestedDict):
        """Reformats a nested dictionary into a flattened dictionary
        If the argument parent_key and sep aren't passed in, the default underscore is used
        Parameters
        ----------
        d: nested dictionary
            ex. {'geotrace_example': {'type': 'LineString', 'coordinates': [[-98.318627, 38.548165, 0]}}
        Returns
        ------
        dict(items) - dictionary
            ex. {'type': 'LineString', 'coordinates': [[-98.318627, 38.548165, 0]}
        """

        new_dict = {}
        for rkey,val in nestedDict.items():
            key = rkey
            if isinstance(val, dict):
                new_dict.update(self.flattenValues(val))
            else:
                new_dict[key] = val
        return new_dict

    def importData(self, layer, selectedForm, doImportData=True):
        """Imports user selected form from server """

        # from central
        user = username_odk
        project_id = self.project_id
        password = password_odk
        c_url = url_odk
        if not c_url:
            print("Enter url in OdkAuth.ini file")
            return None, None
        data = {'email': user, 'password': password}
        headers = {"Content-Type": "application/json"}
        requests.packages.urllib3.disable_warnings()
        selectedFormName = ""
        form_response = requests.get(c_url + "v1/projects/" + str(project_id) + "/forms/",
                                     headers={"Authorization": "Bearer " + self.usertoken})
        for form in form_response.json():
            if form["enketoOnceId"] == selectedForm:
                selectedFormName = form["name"]
                self.form_name = selectedFormName
        try:
            response = requests.get(c_url + 'v1/projects/' + str(project_id) + '/forms/' + selectedFormName + '.xml',
                                    headers={"Authorization": "Bearer " + self.usertoken})
        except:
            print("Invalid url,username or password")
            return
        if response.status_code == 200:
            xml = response.content
            print(xml)
            self.layer_name, self.version, self.geoField, self.fields = self.updateLayerXML(layer, xml)
            # layer.setName(self.layer_name)
            # self.collectData(layer, selectedForm, doImportData, self.layer_name, self.version, self.geoField)
        else:
            print("not able to connect to server")

    def updateLayerXML(self,layer,xml):

        """
        In this function we are trying to extract the following:

        1. tite of the selected form
        2. instance of the selected form
        3. version of the selected form
        4. field names and field types from the <bind> tag in the XML response
        5. qgstype, config of the attribute type using qtype function which is user defined is also extracted
        6. extract the geoField from all the fields and set the isHidden of all the fields as false.
        7. Next we pass on layer, fieldNames, qgstypes, configs of all the fields to updateFields function

        :param layer:
        :param xml:
        :return:
        layer_name,version,geoField,fields
        """

        geoField=''
        ns='{http://www.w3.org/2002/xforms}'
        nsh='{http://www.w3.org/1999/xhtml}'
        root= ET.fromstring(xml)
        #key= root[0][1][0][0].attrib['id']
        layer_name=root[0].find(nsh+'title').text
        instance=root[0][1].find(ns+'instance')
        fields={}
        #topElement=root[0][1][0][0].tag.split('}')[1]
        try:
            version=instance[0].attrib['version']
        except:
            version='null'
#        print('form name is '+ layer_name)
#        print (root[0][1].findall(ns+'bind'))
        for bind in root[0][1].findall(ns+'bind'):
            attrib=bind.attrib
            fieldName= attrib['nodeset'].split('/')[-1]
            try:
                fieldType=attrib['type']
            except:
                continue
            fields[fieldName]=fieldType
            # print('attrib type is',attrib['type'])
            qgstype,config = qtype(attrib['type'])
#            print ('first attribute'+ fieldName)
            inputs=root[1].findall('.//*[@ref]')
            if fieldType[:3]!='geo':
                #print('creating new field:'+ fieldName)
                isHidden= True
                if fieldName=='instanceID':
                    fieldName='ODKUUID'
                    fields[fieldName]=fieldType
                    isHidden= False
                for input in inputs:
                    if fieldName == input.attrib['ref'].split('/')[-1]:
                        isHidden= False
                        break
                if isHidden:
                    # print('Reached Hidden')
                    config['type']='Hidden'
            else:
                geoField=fieldName
                # print('geometry field is =',fieldName)
                continue
            self.updateFields(layer,fieldName,qgstype,config)
        return layer_name,version,geoField,fields

    def updateFields(self, layer, text='ODKUUID', q_type=QVariant.String, config={}):

        """

        This function writes the attribute names and types along with the config to the shapefile.
        :param layer:
        :param text:
        :param q_type:
        :param config:
        :return:
        """

        flag = True
        for field in layer.fields():

            if field.name()[:10] == text[:10]:
                flag = False
                # print("not writing fields")
        if flag:
            uuidField = QgsField(text, q_type)
            if q_type == QVariant.String:
                uuidField.setLength(300)
            layer.dataProvider().addAttributes([uuidField])
            layer.updateFields()
        fId = layer.dataProvider().fieldNameIndex(text)
        try:
            if config['type'] == 'Hidden':
                # print('setting hidden widget')
                layer.setEditorWidgetSetup(fId, QgsEditorWidgetSetup("Hidden", config))
                return
        except Exception as e:
            # print(e)
            pass
        if config == {}:
            return
        # print('now setting external resource widget')
        layer.setEditorWidgetSetup(fId, QgsEditorWidgetSetup("ExternalResource", config))
        # print("done")

"""
*************************************************************************************************
                               KOBO ---> TESTING getFormList
*************************************************************************************************
"""
data_kobo = ImportOdk()

try:
    print(data_kobo.getFormList())
except:
    print("Invalid credentials entered")

"""
*************************************************************************************************
                               KOBO ---> TESTING importData
*************************************************************************************************
"""
layer = QgsVectorLayer('/Users/saimanojappalla/Desktop/OdkShpTest/test.shp', "new", "ogr")
data_kobo.importData(layer, last_selected_form_id)