
# Developing a PyQGIS Script to Automate the Process of Ingestion of Kobo Toolbox and ODK Central Data into GeoServer

Data is fuel for research. Humongous amounts of GIS data are being collected, and the real time analysis of the data is essential to make the right decisions and take quick actions when necessary. Many data collection apps are available, ranging from free to paid subscriptions. Kobo Toolbox and ODK Central were chosen among this plethora of apps since they are free and provide robust API access. In this project, a PyQGIS standalone script was developed to import the collected data into a shapefile or a PostGIS layer from the Kobo or ODK Central server, publish it to GeoServer and update the data and extents in the GeoServer after publishing it once. Testing the script was executed by considering a simple use case where a form was created to collect the soil temperature data. Then, the interpolated maps were generated in real time using the data collected and were named based on the time at which they were collected. This real time data can be analyzed in many ways depending on the user’s requirement, and the results can be incorporated into the decision-making process to make the right decisions at the right time.




## Acknowledgements

 - [QRealTime (Shiva Reddy Koti, Prabhakar Alok Varma)](https://shivareddyiirs.github.io/QRealTime/)
 - [geoserver-rest api (Tek Bahadur Kshetri)](https://pypi.org/project/geoserver-rest/)


## Software Used

 Kobo Toolbox, ODK Central, QGIS



## Features

- Import the data collected using ODK Central and Kobo Toolbox into shapefile or a PostGIS table.
- Publish and update (extent) the layer in GeoServer simultaneously.
- Automate the above two processes and perform some analysis.


## How to use the repository ?
1) This repository has a ini folder where four ini files are stored which is changed by the user as well as the code. The following files are present inside the ini folder.

- #### GeoserverAuth.ini
    This file has three sections; where the first section stores the credentials required to authenticate the GeoServer. The second section deals with shapefiles and stores the workspace name, store name, shapefile path, and publish count. Finally, the third section deals with the PostGIS database and will store the workspace name, store name, and publish count information.
- #### KoboAuth.ini
    This ini file has two sections. The first section stores the Kobo Collect credentials of the user. The second section gets updated when the user runs the python code used to update the forms list. Finally, the last used form is updated by the user.
- #### OdkAuth.ini
    This ini file has one section where the authentication information entered by the user, the last used project, and the last submission reside. The other sections appear when the user runs the code to update the project and form data.
- #### PgAuth.ini
    This ini file has only one section where the user enters the credentials to connect to the PostGIS table.

2) This repository also holds two python files KoboFormsList.py and OdkFormsList.py

- #### KoboFormsList.py:
    This python file has the getFormsList function, which is used to fetch the form names and their ids in the selected project in the Kobo Server. An API call is made to get the forms list.
- #### OdkFormsList.py:
    This python file has the getFormsList function, which is used to fetch the form names and their ids in the selected project in ODK Central Server. An API call is made to get the forms list.

3) This repository has four main python files that should be run by the user depending on the requirement.

- #### DownloadToPgAndPublishKobo.py: 
    This file is used import data from the Kobo server into the PostGIS database and publish the layer to GeoServer.
- #### DownloadToPgAndPublishOdk.py:
    This file is used import data from the ODK server into the PostGIS database and publish the layer to GeoServer.
- #### DownloadToShpAndPublishKobo.py:
    This file is used import data from the Kobo server into the shapefile and publish the layer to GeoServer.
- #### DownloadToShpAndPublishOdk.py: 
    This file is used import data from the ODK server into the shapefile and publish the layer to GeoServer.

4) This repository also has a folder named xml that hosts four xml files which automatically gets updated by the code and are used to update the extent of the layeri n GeoServer.
## Test Results

The above scripts are tested for generating the interpolated maps in real time while the soil temperature values are being collected. The script was successful in importing the data from the server, publising the data to GeoServer, updating the extent and analysing the data. The following is the link to view the screen recording of the working of the script.

[YouTube Link of Screen Recording](https://youtu.be/cjuAuGZGh4E)
