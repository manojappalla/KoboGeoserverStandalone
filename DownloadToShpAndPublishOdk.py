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
last_project_used_odk = odk['Projects ODK']['last used']

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