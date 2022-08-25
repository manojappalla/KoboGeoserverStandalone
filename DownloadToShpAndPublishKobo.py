#!/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3.8
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

# KOBO VARIABLES
kobo = configparser.ConfigParser()
kobo.read('KoboAuth.ini')

url_kobo = kobo['Kobo Credentials']['url']
username_kobo = kobo['Kobo Credentials']['username']
password_kobo = kobo['Kobo Credentials']['password']
last_submission_kobo = kobo['Kobo Credentials']['last submission']
form_feature_count_kobo = 0

# KOBO-GEOSERVER VARIABLES
shp_workspace_name_kobo = config['Shapefile Workspace Store']['workspace_name_kobo']
shp_store_name_kobo = config['Shapefile Workspace Store']['store_name_kobo']
shp_path_kobo = config['Shapefile Workspace Store']['shp_path_kobo']
no_of_times_published_kobo = int(config['Shapefile Workspace Store']['publish_count_kobo'])
# layer_name = shp_path_kobo.split('/')[-1].split('.')[0]

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


# CREATE THE IMPORT CLASS
class ImportKobo:

    def __init__(self):
        self.kobo_url = url_kobo
        self.kobo_username = username_kobo
        self.kobo_password = password_kobo


    def getAuth(self):
        auth = requests.auth.HTTPDigestAuth(self.kobo_username,self.kobo_password)
        return auth


    def getValue(self,key, newValue = None):
        # print("searching in setting parameter",key)
        for row in range (0,self.rowCount()):
            # print(" parameter is",self.item(row,0).text())
            if self.item(row,0).text() == key:
                if newValue:
                    self.item(row, 1).setText(str(newValue))
                    # print("setting new value",newValue)
                    self.setup() #store to settings
                value=self.item(row,1).text().strip()
                if value:
                    if key=='url':
                        if not value.endswith('/'):
                            value=value+'/'
                    return value


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

        """
        This function will return the dictionary of all the forms present in the kobotoolbox in json format

        :return:
        dictionary containing name of the form as key and id as value
        Example: ({'test': 'aDHQqdStRmoRUwSZJb5P35', 'iirs_buildings': 'aumGeYCKpLmoK6jkcDgcUv'}, <Response [200]>)
        """

        user = self.kobo_username
        password = self.kobo_password
        turl = self.kobo_url
        proxies = self.getproxiesConf()

        if turl:
            url=turl+'api/v2/assets'
        else:
            # print("Enter correct url.")
            return None, None

        para={'format':'json'}
        keyDict={}
        questions = []

        try:
            response = requests.get(url, proxies=proxies, auth=(user, password), params=para)
            forms = response.json()
            for form in forms['results']:
                if form['asset_type'] == 'survey' and form['deployment__active'] == True:
                    keyDict[form['name']] = form['uid']
            return keyDict
        except:
            # self.iface.messageBar().pushCritical(self.tag, self.tr("Invalid url username or password"))
            # print("Invalid username or password")
            return None, None


    def importData(self,layer,selectedForm,doImportData=True):

        """
        This function accesses the XML response received from the get request using the following url
                        url = turl + '/assets/' + selectedForm
        The XML response returned is passed to the updateLayerXML() function.

        :param layer:
        :param selectedForm:
        :param doImportData:
        :return:
        No return value
        """

        #from kobo branchQH
        user=self.kobo_username
        password=self.kobo_password
        turl=self.kobo_url
        if turl:
            url=turl+'/assets/'+selectedForm
        else:
            # print("URL is not entered.")
            pass
        para={'format':'xml'}
        requests.packages.urllib3.disable_warnings()
        try:
            response= requests.request('GET',url,proxies=self.getproxiesConf(),auth=(user,password),verify=False,params=para)
        except:
            # print("Invalid url,username or password")
            return
        if response.status_code==200:
            xml=response.content

            self.layer_name,self.version, self.geoField,self.fields= self.updateLayerXML(layer,xml)
            layer.setName(self.layer_name)
            self.user=user
            self.password=password
            # print("calling collect data")
            self.collectData(layer,selectedForm,doImportData,self.layer_name,self.version,self.geoField)
        else:
            # print("not able to connect to server")
            pass

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
        self.turl = self.kobo_url
        self.auth = self.getAuth()
        self.lastID = last_submission_kobo
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
        self.comp(self.getTable())


    def getTable(self):
        try:
            # print("get table started")
            # task.setProgress(10.0)
            #requests.packages.urllib3.disable_warnings()
            url=self.turl
            #task.setProgress(30.0)
            lastSub=""
            if not self.isImportData:
                lastSub=self.lastID
            urlData=url+'/api/v2/assets/'+self.xFormKey+'/data/'
            table=[]
            response=None
            if not lastSub:
                para={'format':'json'}
                try:
                    response = requests.get(urlData,proxies=self.proxyConfig,auth=(self.user,self.password),params=para,verify=False)
                except:
                    # print("not able to connect to server",urlData)
                    return {'response':response, 'table':table}
                # print('requesting url is'+response.url)
            else:
                query_param={"_id": {"$gt":int(lastSub)}}
                jsonquery=json.dumps(query_param)
                # print('query_param is'+jsonquery)
                para={'query':jsonquery,'format':'json'}
                try:
                    response = requests.get(urlData,proxies=self.proxyConfig,auth=(self.user,self.password),params=para,verify=False)
                    # print('requesting url is'+response.url)
                except:
                    # print("not able to connect to server",urlData)
                    return {'response':response, 'table':table,'lastID':None}
            #task.setProgress(50)
            data=response.json()
            #print(data,type(data))
            subList=[]
            # print("no of submissions are",data['count'])
            global form_feature_count_kobo
            form_feature_count_kobo = data['count']
            if data['count']==0:
                return {'response':response, 'table':table}
            for submission in data['results']:
                submission['ODKUUID']=submission['meta/instanceID']
                subID=submission['_id']
                binar_url=""
                for attachment in submission['_attachments']:
                    binar_url=attachment['download_url']
                #subTime_datetime=datetime.datetime.strptime(subTime,'%Y-%m-%dT%H:%M:%S')
                subList.append(subID)
                for key in list(submission):
                    # print(key)
                    if key == self.geoField:
                        # print (self.geoField)
                        continue
                    if key not in self.fields:
                        submission.pop(key)
                    else:
                        if self.fields[key]=="binary":
                            submission[key]=binar_url
                table.append(submission)
            #task.setProgress(90)
            if len(subList)>0:
                lastSubmission=max(subList)
            # print({'response':response, 'table':table,'lastID':lastSubmission})
            return {'response':response, 'table':table,'lastID':lastSubmission}
        except Exception as e:
            # print("exception occured in gettable",e)
            return {'response':None, 'table':None,'lastID':None}


    def comp(self,result):
        # if exception:
        #     print("exception in task execution")
        response=result['response']
        remoteTable=result['table']
        # print(remoteTable)
        lastID=result['lastID']
        if response.status_code == 200:
            # print ('after task finished before update layer')
            if remoteTable:
                # print ('task has returned some data')
                self.updateLayer(self.layer,remoteTable,self.geoField)
                # print("lastID is",lastID)
                kobo['Kobo Credentials']['last submission'] = str(lastID)
                with open('KoboAuth.ini', 'w') as configfile:
                    kobo.write(configfile)
                # print(kobo['Kobo Credentials']['last submission'])
                print("Data imported Successfully")
        else:
            print("Not able to collect data.")


    def updateLayer(self, layer, dataDict, geoField=''):
        # print "UPDATING N.",len(dataDict),'FEATURES'
        self.processingLayer = layer
        QgisFieldsList = [field.name() for field in layer.fields()]
        # layer.beginEditCommand("ODK syncronize")
        #        layer.startEditing()
        type = layer.geometryType()
        geo = ['POINT', 'LINE', 'POLYGON']
        layerGeo = geo[type]

        uuidList = self.getUUIDList(self.processingLayer)

        newQgisFeatures = []
        fieldError = None
        # print('geofield is', geoField)
        for odkFeature in dataDict:
            # print(odkFeature)
            id = None
            try:
                id = odkFeature['ODKUUID']
                # print('odk id is', id)
            except:
                # print('error in reading ODKUUID')
                pass
            try:
                if not id in uuidList:
                    qgisFeature = QgsFeature()
                    # print("odkFeature", odkFeature)
                    wktGeom = self.guessWKTGeomType(odkFeature[geoField])
                    # print(wktGeom)
                    if wktGeom[:3] != layerGeo[:3]:
                        # print(wktGeom, 'is not matching' + layerGeo)
                        continue
                    qgisGeom = QgsGeometry.fromWkt(wktGeom)
                    # print('geom is', qgisGeom)
                    qgisFeature.setGeometry(qgisGeom)
                    qgisFeature.initAttributes(len(QgisFieldsList))
                    for fieldName, fieldValue in odkFeature.items():
                        if fieldName != geoField:
                            try:
                                qgisFeature.setAttribute(QgisFieldsList.index(fieldName[:10]), fieldValue)
                            except:
                                fieldError = fieldName

                    newQgisFeatures.append(qgisFeature)

            except Exception as e:
                # print('unable to create', e)
                pass
            # print(dataDict)
        try:
            geo = Geoserver(url_geoserver, username_geoserver, password_geoserver)
            with edit(layer):
                layer.addFeatures(newQgisFeatures)

            # PUBLISHES ONLY IF THE NO OF SUBMISSIONS IN THE FORM ARE GREATER THAN OR EQUAL TO 2 AND THE NO OF TIMES PUBLISHED COUNT IS 0
            if (form_feature_count_kobo >= 2 and no_of_times_published_kobo == 0):
                layer_name = shp_path_kobo.split('/')[-1].split('.')[0]
                geo.create_datastore(name=shp_store_name_kobo, path=shp_path_kobo, workspace=shp_workspace_name_kobo)
                geo.publish_featurestore(workspace=shp_workspace_name_kobo, store_name=shp_store_name_kobo, pg_table=layer_name)
            config['Shapefile Workspace Store']['publish_count_kobo'] = str(1)
            with open('GeoserverAuth.ini', 'w') as configfile:
                config.write(configfile)
        except:
            # print("Stop layer editing and import again")
            pass
        self.processingLayer = None



    def getUUIDList(self,lyr):
        uuidList = []
        uuidFieldName=None
        QgisFieldsList = [field.name() for field in lyr.fields()]
        for field in QgisFieldsList:
            if 'UUID' in field:
                uuidFieldName =field
        if uuidFieldName:
            # print(uuidFieldName)
            for qgisFeature in lyr.getFeatures():
                uuidList.append(qgisFeature[uuidFieldName])
        # print (uuidList)
        return uuidList


    def guessWKTGeomType(self, geom):
        if geom:
            coordinates = geom.split(';')
        else:
            return 'error'
        #        print ('coordinates are '+ coordinates)
        firstCoordinate = coordinates[0].strip().split(" ")
        if len(firstCoordinate) < 2:
            return "invalid", None
        coordinatesList = []
        for coordinate in coordinates:
            decodeCoord = coordinate.strip().split(" ")
            #            print 'decordedCoord is'+ decodeCoord
            try:
                coordinatesList.append([decodeCoord[0], decodeCoord[1]])
            except:
                pass
        if len(coordinates) == 1:

            reprojectedPoint = self.transformToLayerSRS(
                QgsPoint(float(coordinatesList[0][1]), float(coordinatesList[0][0])))
            return "POINT(%s %s)" % (reprojectedPoint.x(), reprojectedPoint.y())  # geopoint
        else:
            coordinateString = ""
            for coordinate in coordinatesList:
                reprojectedPoint = self.transformToLayerSRS(QgsPoint(float(coordinate[1]), float(coordinate[0])))
                coordinateString += "%s %s," % (reprojectedPoint.x(), reprojectedPoint.y())
            coordinateString = coordinateString[:-1]
        if coordinatesList[0][0] == coordinatesList[-1][0] and coordinatesList[0][1] == coordinatesList[-1][1]:
            return "POLYGON((%s))" % coordinateString  # geoshape #geotrace
        else:
            return "LINESTRING(%s)" % coordinateString


    def transformToLayerSRS(self, pPoint):
        # transformation from the current SRS to WGS84
        crsDest = self.processingLayer.crs () # get layer crs
        crsSrc = QgsCoordinateReferenceSystem("EPSG:4326")  # WGS 84
        xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
        try:
            return QgsPoint(xform.transform(pPoint))
        except :
            return QgsPoint(xform.transform(QgsPointXY(pPoint)))

"""
*************************************************************************************************
                               KOBO ---> TESTING getFormList
*************************************************************************************************
"""
data_kobo = ImportKobo()

try:
    data_kobo.getFormList()
except:
    print("Invalid credentials entered")


"""
*************************************************************************************************
                               KOBO ---> TESTING importData, updateLayerXML, updateFields
*************************************************************************************************
"""

# TODO: Create one empty shapefile and pass it as an argument to the importData function

layer = QgsVectorLayer(shp_path_kobo, "new", "ogr")
# QgsProject.instance().addMapLayer(layer)
selected_form = kobo['Forms List']['last used']
data_kobo.importData(layer, selected_form)
# try:
#     while True:
#         data_kobo.importData(layer, selected_form)
# except KeyboardInterrupt:
#     pass




