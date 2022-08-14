# IMPORT THE LIBRARIES
from Geoserver import Geoserver
import configparser


# DEFINE THE Auth CLASS
class Auth:

    def __init__(self, url, username, password, workspace_name):
        self.url = url
        self.username = username
        self.password = password
        self.workspace_name = workspace_name


    def authenticate(self):

        """
        This function will take url, username, password, and workspace name as input and will check whether the workspace
        already exists or not. This can also act as an authentication. This function is called inside storeAuthAndAuthenticate()
        function.
        :return:
        """

        config = configparser.ConfigParser()
        config.read('geoserver_auth.ini')

        url = config['Geoserver Credentials']['Url']
        username = config['Geoserver Credentials']['Username']
        password = config['Geoserver Credentials']['password']
        workspace_bool = None

        self.geo = Geoserver(url, username=username, password=password)
        workspaces, chk = self.geo.get_workspaces()

        if chk:
            print("Authenticated...")
            for name in workspaces['workspaces']['workspace']:
                if name['name'] == self.workspace_name:
                    print("Workspace is already existing")
                    workspace_bool = False
                else:
                    workspace_bool = True

        else:
            print("Wrong Credentials. Please enter correct credentials for geoserver.")

        return workspace_bool


    def storeAuthAndAuthenticate(self):

        """
        This function first checks the ini file for the similarity of the entered information and writes it if it is not the same
        else it prints that the informations already exists and authenticates the user using the authenticate() function.
        :return:
        """

        config = configparser.ConfigParser()
        config.read('geoserver_auth.ini')

        if ((config['Geoserver Credentials']['Url'] != self.url) or (config['Geoserver Credentials']['Username'] != self.username) or (config['Geoserver Credentials']['password'] != self.password)):
            config['Geoserver Credentials']['Url'] = self.url
            config['Geoserver Credentials']['Username'] = self.username
            config['Geoserver Credentials']['password'] = self.password
            with open('geoserver_auth.ini', 'w') as configfile:
                config.write(configfile)
        else:
            print("Information already exists...")

        return self.authenticate()


    def createWorkspace(self):

        """
        This function is used to create a workspace after authenticating the user.
        :return:
        """

        if self.storeAuthAndAuthenticate():
            self.geo.create_workspace(workspace=self.workspace_name)
            print("The workspace {} has been created.".format(self.workspace_name))






"""
*************************************************************************************************
                                TESTING
*************************************************************************************************
"""


# url = input("Enter url: ")
# username = input("Enter username: ")
# password = input("Enter password: ")
# workspace_name = input("Enter workspace name: ")
#
# auth = Auth(url, username, password, workspace_name)
# auth.createWorkspace()