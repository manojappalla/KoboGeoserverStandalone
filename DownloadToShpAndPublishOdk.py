# IMPORT ALL THE NECESSARY LIBRARIES
import os
import datetime

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

    def getAuth(self):
        auth = requests.auth.HTTPDigestAuth(username_odk,password_odk)
        return auth

    def getproxiesConf(self):

        """
        This function is used to configure all the proxy settings.
        :return:
        """
        s = QSettings()  # getting proxy from qgis options settings
        proxyEnabled = s.value("proxy/proxyEnabled", "")
        proxyType = s.value("proxy/proxyType", "")
        proxyHost = s.value("proxy/proxyHost", "")
        proxyPort = s.value("proxy/proxyPort", "")
        proxyUser = s.value("proxy/proxyUser", "")
        proxyPassword = s.value("proxy/proxyPassword", "")
        if proxyEnabled == "true" and proxyType == 'HttpProxy':  # test if there are proxy settings
            proxyDict = {
                "http": "http://%s:%s@%s:%s" % (proxyUser, proxyPassword, proxyHost, proxyPort),
                "https": "http://%s:%s@%s:%s" % (proxyUser, proxyPassword, proxyHost, proxyPort)
            }
            return proxyDict
        else:
            return None


    """
    *************************************************************************************************
                                    PART-1
    *************************************************************************************************
    """
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
            self.collectData(layer, selectedForm, doImportData, self.layer_name, self.version, self.geoField)
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
                                    PART-2
    *************************************************************************************************
    """

    def collectData(self, layer, xFormKey, doImportData=False, topElement='', version=None, geoField=''):
        #        if layer :
        #            print("layer is not present or not valid")
        #            return
        def testc(exception, result):
            if exception:
                # print("task raised exception")
                pass
            else:
                # print("Success", result[0])
                # print("task returned")
                pass

        self.updateFields(layer)
        self.layer = layer
        self.turl = url_odk
        self.auth = self.getAuth()
        self.lastID = last_submission_odk
        self.proxyConfig = self.getproxiesConf()
        self.xFormKey = xFormKey
        self.isImportData = doImportData
        self.topElement = topElement
        self.version = version
        # print("task is being created")
        # self.task1 = QgsTask.fromFunction('downloading data', self.getTable, on_finished=self.comp)
        # print("task is created")
        # print("task status1 is  ", self.task1.status())
        # QgsApplication.taskManager().addTask(self.task1)
        # print("task added to taskmanager")
        # print("task status2 is  ", self.task1.status())
        # # task1.waitForFinished()
        # print("task status3 is  ", self.task1.status())
        # response, remoteTable = self.getTable(xFormKey,importData,topElement,version)
        print(self.getTable())
        # self.comp(self.getTable())

    def getTable(self):
        """Retrieves data from form table, and filters out only the necessary fields
        Returns
        ------
        response, list
            response1 - HTTP response
                response containing original form table data
            table - list
                contains filtered fields
        """

        user=username_odk
        password=password_odk
        requests.packages.urllib3.disable_warnings()
        # hard coded url is being used
        url=url_odk
        # print(url)
        storedGeoField = self.geoField
        lastSub=""
        if not self.isImportData:
            try:
                lastSub=last_submission_odk
            except:
                print("error")
        url_submissions=url + "v1/projects/"+str(self.project_id)+"/forms/" + self.form_name
        url_data=url + "v1/projects/"+str(self.project_id)+"/forms/" + self.form_name + ".svc/Submissions"
        #print('urldata is '+url_data)
        response = requests.get(url_submissions, headers={"Authorization": "Bearer " + self.usertoken, "X-Extended-Metadata": "true"})
        response1 = requests.get(url_data, headers={"Authorization": "Bearer " + self.usertoken})
        submissionHistory=response.json()
        # json produces nested dictionary contain all table data
        data=response1.json()
        # print(data)
        subTimeList=[]
        table=[]
        if submissionHistory['submissions']==0:
            return response1, table
        for submission in data['value']:
            formattedData = self.flattenValues(submission)
            formattedData[storedGeoField] = formattedData.pop('coordinates')
            formattedData['ODKUUID'] = formattedData.pop('__id')
            subTime = formattedData['submissionDate']
            subTime_datetime=datetime.datetime.strptime(subTime[0: subTime.index('.')],'%Y-%m-%dT%H:%M:%S')
            subTimeList.append(subTime_datetime)
            stringversion = ''
            coordinates = formattedData[storedGeoField]
            # removes brackets to format coordinates in a string separated by spaces (ex. "38.548165 -98.318627 0")
            if formattedData['type'] == 'Point':
                latitude = coordinates[1]
                coordinates[1] = coordinates[0]
                coordinates[0] = latitude
                for val in formattedData[storedGeoField]:
                    stringversion+= str(val) + ' '
            else:
                count = 1
                for each_coor in coordinates:
                    temp = ""
                    #converting current (longitude, latitude) coordinate to (latitude, longitude) for accurate graphing
                    latitude = each_coor[1]
                    each_coor[1] = each_coor[0]
                    each_coor[0] = latitude
                    for val in each_coor:
                        temp += str(val) + " "
                    stringversion += str("".join(temp.rstrip()))
                    if count != len(coordinates):
                        stringversion += ";"
                    count+=1
            formattedData[storedGeoField] = stringversion
            if formattedData['attachmentsPresent']>0:
                url_data1 = url + "v1/projects/"+str(self.project_id)+"/forms/" + self.form_name +"/submissions"+"/"+formattedData['ODKUUID']+ "/attachments"
                media_links_url = url + "#/dl/projects/"+str(self.project_id)+"/forms/" + self.form_name +"/submissions"+"/"+formattedData['ODKUUID']+ "/attachments"
                # print("making attachment request"+url_data1)
                attachmentsResponse = requests.get(url_data1, headers={"Authorization": "Bearer " + self.usertoken})
                # print("url response is"+ str(attachmentsResponse.status_code))
                for attachment in attachmentsResponse.json():
                    binar_url= media_links_url +"/"+str(attachment['name'])
            #subTime_datetime=datetime.datetime.strptime(subTime,'%Y-%m-%dT%H:%M:%S')
            #subTimeList.append(subTime_datetime)
            for key in list(formattedData):
                # print(key)
                if key == self.geoField:
                    # print (self.geoField)
                    continue
                if key not in self.fields:
                    formattedData.pop(key)
                else:
                    if self.fields[key]=="binary":
                        formattedData[key]=binar_url
            # print("submission parsed"+str(formattedData))
            table.append(formattedData)
        if len(subTimeList)>0:
            lastSubmission=max(subTimeList)
            lastSubmission=datetime.datetime.strftime(lastSubmission,'%Y-%m-%dT%H:%M:%S')+"+0000"
            # self.getValue(self.tr('last Submission'),lastSubmission)
        return {'response':response1, 'table':table,'lastID':lastSubmission}

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