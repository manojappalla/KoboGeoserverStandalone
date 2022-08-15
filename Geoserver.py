# inbuilt libraries
import os
from typing import List, Optional, Set

# third-party libraries
import requests
from xmltodict import parse, unparse

# custom functions
from supports import prepare_zip_file


# call back class for reading the data
class DataProvider(object):
    def __init__(self, data):
        self.data = data
        self.finished = False

    def read_cb(self, size):
        assert len(self.data) <= size
        if not self.finished:
            self.finished = True
            return self.data
        else:
            # Nothing more to read
            return ""

# callback class for reading the files
class FileReader:
    def __init__(self, fp):
        self.fp = fp

    def read_callback(self, size):
        return self.fp.read(size)


class Geoserver:
    """
    Attributes
    ----------
    service_url : str
        The URL for the GeoServer instance.
    username : str
        Login name for session.
    password: str
        Password for session.
    """

    def __init__(
        self,
        service_url: str = "http://localhost:8080/geoserver",  # default deployment url during installation
        username: str = "admin",  # default username during geoserver installation
        password: str = "geoserver",  # default password during geoserver installation
    ):
        self.service_url = service_url
        self.username = username
        self.password = password

        # private request method to reduce repetition of putting auth(username,password) in all requests call. DRY principle

    def _requests(self, method: str, url: str, **kwargs) -> requests.Response:
        if method == "post":
            return requests.post(url, auth=(self.username, self.password), **kwargs)
        elif method == "get":
            return requests.get(url, auth=(self.username, self.password), **kwargs)
        elif method == "put":
            return requests.put(url, auth=(self.username, self.password), **kwargs)
        elif method == "delete":
            return requests.delete(url, auth=(self.username, self.password), **kwargs)


    def get_manifest(self):
        """
        Returns the manifest of the geoserver. The manifest is a JSON of all the loaded JARs on the GeoServer server.

        """
        try:
            url = "{}/rest/about/manifest.json".format(self.service_url)
            r = requests.get(url, auth=(self.username, self.password))
            return r.json()

        except Exception as e:
            return "get_manifest error: ", e


    def get_version(self):
        """
        Returns the version of the geoserver as JSON. It contains only the details of the high level components: GeoServer, GeoTools, and GeoWebCache
        """
        try:
            url = "{}/rest/about/version.json".format(self.service_url)
            r = self._requests("get", url)
            return r.json()

        except Exception as e:
            return "get_version error: ", e


    def get_status(self):
        """
        Returns the status of the geoserver. It shows the status details of all installed and configured modules.
        """
        try:
            url = "{}/rest/about/status.json".format(self.service_url)
            r = requests.get(url, auth=(self.username, self.password))
            return r.json()

        except Exception as e:
            return "get_status error: ", e

    def get_system_status(self):
        """
        It returns the system status of the geoserver. It returns a list of system-level information. Major operating systems (Linux, Windows and MacOX) are supported out of the box.
        """
        try:
            url = "{}/rest/about/system-status.json".format(self.service_url)
            r = requests.get(url, auth=(self.username, self.password))
            return r.json()

        except Exception as e:
            return "get_system_status error: ", e

    def reload(self):
        """
        Reloads the GeoServer catalog and configuration from disk.

        This operation is used in cases where an external tool has modified the on-disk configuration.
        This operation will also force GeoServer to drop any internal caches and reconnect to all data stores.
        curl -X POST http://localhost:8080/geoserver/rest/reload -H  "accept: application/json" -H  "content-type: application/json"
        """
        try:
            url = "{}/rest/reload".format(self.service_url)
            r = requests.post(url, auth=(self.username, self.password))
            return "Status code: {}".format(r.status_code)

        except Exception as e:
            return "reload error: {}".format(e)

    def reset(self):
        """
        Resets all store, raster, and schema caches. This operation is used to force GeoServer to drop all caches and
        store connections and reconnect to each of them the next time they are needed by a request. This is useful in
        case the stores themselves cache some information about the data structures they manage that may have changed
        in the meantime.
        curl -X POST http://localhost:8080/geoserver/rest/reset -H  "accept: application/json" -H  "content-type: application/json"
        """
        try:
            url = "{}/rest/reset".format(self.service_url)
            r = requests.post(url, auth=(self.username, self.password))
            return "Status code: {}".format(r.status_code)

        except Exception as e:
            return "reload error: {}".format(e)


    # _______________________________________________________________________________________________
    #
    #      WORKSPACES
    # _______________________________________________________________________________________________
    #

    def get_default_workspace(self):
        """
        Returns the default workspace.
        """
        try:
            url = "{}/rest/workspaces/default".format(self.service_url)
            r = requests.get(url, auth=(self.username, self.password))
            return r.json()

        except Exception as e:
            return "get_default_workspace error: {}".format(e)

    def get_workspace(self, workspace):
        """
        get name  workspace if exist
        Example: curl -v -u admin:admin -XGET -H "Accept: text/xml"  http://localhost:8080/geoserver/rest/workspaces/acme.xml
        """
        try:
            payload = {"recurse": "true"}
            url = "{}/rest/workspaces/{}.json".format(self.service_url, workspace)
            r = requests.get(url, auth=(self.username, self.password), params=payload)
            if r.status_code == 200:
                return r.json()
            else:
                return None

        except Exception as e:
            return "Error: {}".format(e)

    def get_workspaces(self):
        """
        Returns all the workspaces.
        """
        try:
            url = "{}/rest/workspaces".format(self.service_url)
            r = requests.get(url, auth=(self.username, self.password))
            return r.json(), True

        except Exception as e:
            return "get_workspaces error: {}".format(e), False

    def set_default_workspace(self, workspace: str):
        """
        Set the default workspace.
        """
        try:
            url = "{}/rest/workspaces/default".format(self.service_url)
            data = "<workspace><name>{}</name></workspace>".format(workspace)
            print(url, data)
            r = self._requests(
                "put",
                url,
                data=data,
                headers={"content-type": "text/xml"},
            )

            if r.status_code == 200:
                return "Status code: {}, default workspace {} set!".format(
                    r.status_code, workspace
                )

        except Exception as e:
            return "reload error: {}".format(e)

    def create_workspace(self, workspace: str):
        """
        Create a new workspace in geoserver.

        The geoserver workspace url will be same as the name of the workspace.
        """
        try:
            url = "{}/rest/workspaces".format(self.service_url)
            data = "<workspace><name>{}</name></workspace>".format(workspace)
            headers = {"content-type": "text/xml"}
            r = self._requests("post", url, data=data, headers=headers)

            if r.status_code == 201:
                return "{} Workspace {} created!".format(r.status_code, workspace)

            if r.status_code == 401:
                raise Exception("The workspace already exist")

            else:
                raise Exception("The workspace can not be created")

        except Exception as e:
            return "Error: {}".format(e)

    def delete_workspace(self, workspace: str):
        """

        Parameters
        ----------
        workspace : str

        """
        try:
            payload = {"recurse": "true"}
            url = "{}/rest/workspaces/{}".format(self.service_url, workspace)
            r = requests.delete(
                url, auth=(self.username, self.password), params=payload
            )

            if r.status_code == 200:
                return "Status code: {}, delete workspace".format(r.status_code)

            else:
                raise Exception("Error: {} {}".format(r.status_code, r.content))

        except Exception as e:
            return "Error: {}".format(e)


    # _______________________________________________________________________________________________
    #
    #       DATASTORES
    # _______________________________________________________________________________________________
    #

    def get_datastore(self, store_name: str, workspace: Optional[str] = None):
        """
        Return the data store in a given workspace.

        If workspace is not provided, it will take the default workspace
        curl -X GET http://localhost:8080/geoserver/rest/workspaces/demo/datastores -H  "accept: application/xml" -H  "content-type: application/json"
        """
        try:
            if workspace is None:
                workspace = "default"

            url = "{}/rest/workspaces/{}/datastores/{}".format(
                self.service_url, workspace, store_name
            )

            r = self._requests("get", url)
            return r.json()

        except Exception as e:
            return "get_datastores error: {}".format(e)

    def get_datastores(self, workspace: Optional[str] = None):
        """
        List all data stores in a workspace.

        If workspace is not provided, it will listout all the datastores inside default workspace
        curl -X GET http://localhost:8080/geoserver/rest/workspaces/demo/datastores -H  "accept: application/xml" -H  "content-type: application/json"
        """
        try:
            if workspace is None:
                workspace = "default"

            url = "{}/rest/workspaces/{}/datastores.json".format(
                self.service_url, workspace
            )
            r = requests.get(url, auth=(self.username, self.password))
            return r.json()

        except Exception as e:
            return "get_datastores error: {}".format(e)


    # _______________________________________________________________________________________________
    #
    #       LAYERS
    # _______________________________________________________________________________________________
    #

    def get_layer(self, layer_name: str, workspace: Optional[str] = None):
        """
        Returns the layer by layer name.
        """
        try:
            url = "{}/rest/layers/{}".format(self.service_url, layer_name)
            if workspace is not None:
                url = "{}/rest/workspaces/{}/layers/{}".format(
                    self.service_url, workspace, layer_name
                )

            r = self._requests("get", url)
            if r.status_code in [200, 201]:
                return r.json()
            else:
                return None

        except Exception as e:
            return "get_layer error: {}".format(e)

    def get_layers(self, workspace: Optional[str] = None):
        """
        Get all the layers from geoserver
        If workspace is None, it will listout all the layers from geoserver
        """
        try:
            url = "{}/rest/layers".format(self.service_url)

            if workspace is not None:
                url = "{}/rest/workspaces/{}/layers".format(self.service_url, workspace)
            r = requests.get(url, auth=(self.username, self.password))
            return r.json()

        except Exception as e:
            return "get_layers error: {}".format(e)

    def delete_layer(self, layer_name: str, workspace: Optional[str] = None):
        """

        Parameters
        ----------
        layer_name : str
        workspace : str, optional

        """
        try:
            payload = {"recurse": "true"}
            url = "{}/rest/workspaces/{}/layers/{}".format(
                self.service_url, workspace, layer_name
            )
            if workspace is None:
                url = "{}/rest/layers/{}".format(self.service_url, layer_name)

            r = self._requests(method="delete", url=url, params=payload)
            if r.status_code == 200:
                return "Status code: {}, delete layer".format(r.status_code)

            else:
                raise Exception("Error: {} {}".format(r.status_code, r.content))

        except Exception as e:
            return "Error: {}".format(e)


    # _______________________________________________________________________________________________
    #
    #      FEATURES AND DATASTORES
    # _______________________________________________________________________________________________
    #

    def create_datastore(
        self,
        name: str,
        path: str,
        workspace: Optional[str] = None,
        overwrite: bool = False,
    ):
        """
        Create a datastore within the GeoServer.

        Parameters
        ----------
        name : str
            Name of datastore to be created.
            After creating the datastore, you need to publish it by using publish_featurestore function.
        path : str
            Path to shapefile (.shp) file, GeoPackage (.gpkg) file, WFS url
            (e.g. http://localhost:8080/geoserver/wfs?request=GetCapabilities) or directory containing shapefiles.
        workspace : str, optional default value = "default".
        overwrite : bool

        Notes
        -----
        If you have PostGIS datastore, please use create_featurestore function
        """
        if workspace is None:
            workspace = "default"

        if path is None:
            raise Exception("You must provide a full path to the data")

        data_url = "<url>file:{}</url>".format(path)

        if "http://" in path:
            data_url = "<GET_CAPABILITIES_URL>{}</GET_CAPABILITIES_URL>".format(path)

        data = "<dataStore><name>{}</name><connectionParameters>{}</connectionParameters></dataStore>".format(
            name, data_url
        )
        headers = {"content-type": "text/xml"}

        try:
            if overwrite:
                url = "{}/rest/workspaces/{}/datastores/{}".format(
                    self.service_url, workspace, name
                )
                r = self._requests("put", url, data=data, headers=headers)

            else:
                url = "{}/rest/workspaces/{}/datastores".format(
                    self.service_url, workspace
                )
                r = requests.post(
                    url, data, auth=(self.username, self.password), headers=headers
                )

            if r.status_code in [200, 201]:
                return "Data store created/updated successfully"

            else:
                raise Exception(
                    "datastore can not be created. Status code: {}, {}".format(
                        r.status_code, r.content
                    )
                )

        except Exception as e:
            return "Error create_datastore: {}".format(e)

    def publish_featurestore(
        self, store_name: str, pg_table: str, workspace: Optional[str] = None
    ):
        """

        Parameters
        ----------
        store_name : str
        pg_table : str
        workspace : str, optional

        Returns
        -------

        Notes
        -----
        Only user for postgis vector data
        input parameters: specify the name of the table in the postgis database to be published, specify the store,workspace name, and  the Geoserver user name, password and URL
        """
        if workspace is None:
            workspace = "default"

        url = "{}/rest/workspaces/{}/datastores/{}/featuretypes/".format(
            self.service_url, workspace, store_name
        )

        layer_xml = "<featureType><name>{}</name></featureType>".format(pg_table)
        headers = {"content-type": "text/xml"}

        try:
            r = requests.post(
                url,
                data=layer_xml,
                auth=(self.username, self.password),
                headers=headers,
            )
            if r.status_code not in [200, 201]:
                return "{}: Data can not be published! {}".format(
                    r.status_code, r.content
                )

        except Exception as e:
            return "Error: {}".format(e)

    def create_featurestore(
            self,
            store_name: str,
            workspace: Optional[str] = None,
            db: str = "postgres",
            host: str = "localhost",
            port: int = 5432,
            schema: str = "public",
            pg_user: str = "postgres",
            pg_password: str = "admin",
            overwrite: bool = False,
            expose_primary_keys: str = "false",
            description: Optional[str] = None,
            evictor_run_periodicity: Optional[int] = 300,
            max_open_prepared_statements: Optional[int] = 50,
            encode_functions: Optional[str] = "false",
            primary_key_metadata_table: Optional[str] = None,
            batch_insert_size: Optional[int] = 1,
            preparedstatements: Optional[str] = "false",
            loose_bbox: Optional[str] = "true",
            estimated_extends: Optional[str] = "true",
            fetch_size: Optional[int] = 1000,
            validate_connections: Optional[str] = "true",
            support_on_the_fly_geometry_simplification: Optional[str] = "true",
            connection_timeout: Optional[int] = 20,
            create_database: Optional[str] = "false",
            min_connections: Optional[int] = 1,
            max_connections: Optional[int] = 10,
            evictor_tests_per_run: Optional[int] = 3,
            test_while_idle: Optional[str] = "true",
            max_connection_idle_time: Optional[int] = 300,
    ):
        """
        Create PostGIS store for connecting postgres with geoserver.
        Parameters
        ----------
        store_name : str
        workspace : str, optional
        db : str
        host : str
        port : int
        schema : str
        pg_user : str
        pg_password : str
        overwrite : bool
        expose_primary_keys: str
        description : str, optional
        evictor_run_periodicity : str
        max_open_prepared_statements : int
        encode_functions : str
        primary_key_metadata_table : str
        batch_insert_size : int
        preparedstatements : str
        loose_bbox : str
        estimated_extends : str
        fetch_size : int
        validate_connections : str
        support_on_the_fly_geometry_simplification : str
        connection_timeout : int
        create_database : str
        min_connections : int
        max_connections : int
        evictor_tests_per_run : int
        test_while_idle : str
        max_connection_idle_time : int
        Notes
        -----
        After creating feature store, you need to publish it. See the layer publish guidline here: https://geoserver-rest.readthedocs.io/en/latest/how_to_use.html#creating-and-publishing-featurestores-and-featurestore-layers
        """

        url = "{}/rest/workspaces/{}/datastores".format(self.service_url, workspace)

        headers = {"content-type": "text/xml"}

        database_connection = """
                <dataStore>
                <name>{0}</name>
                <description>{1}</description>
                <connectionParameters>
                <entry key="Expose primary keys">{2}</entry>
                <entry key="host">{3}</entry>
                <entry key="port">{4}</entry>
                <entry key="user">{5}</entry>
                <entry key="passwd">{6}</entry>
                <entry key="dbtype">postgis</entry>
                <entry key="schema">{7}</entry>
                <entry key="database">{8}</entry>
                <entry key="Evictor run periodicity">{9}</entry>
                <entry key="Max open prepared statements">{10}</entry>
                <entry key="encode functions">{11}</entry>
                <entry key="Primary key metadata table">{12}</entry>
                <entry key="Batch insert size">{13}</entry>
                <entry key="preparedStatements">{14}</entry>
                <entry key="Estimated extends">{15}</entry>
                <entry key="fetch size">{16}</entry>
                <entry key="validate connections">{17}</entry>
                <entry key="Support on the fly geometry simplification">{18}</entry>
                <entry key="Connection timeout">{19}</entry>
                <entry key="create database">{20}</entry>
                <entry key="min connections">{21}</entry>
                <entry key="max connections">{22}</entry>
                <entry key="Evictor tests per run">{23}</entry>
                <entry key="Test while idle">{24}</entry>
                <entry key="Max connection idle time">{25}</entry>
                <entry key="Loose bbox">{26}</entry>
                </connectionParameters>
                </dataStore>
                """.format(
            store_name,
            description,
            expose_primary_keys,
            host,
            port,
            pg_user,
            pg_password,
            schema,
            db,
            evictor_run_periodicity,
            max_open_prepared_statements,
            encode_functions,
            primary_key_metadata_table,
            batch_insert_size,
            preparedstatements,
            estimated_extends,
            fetch_size,
            validate_connections,
            support_on_the_fly_geometry_simplification,
            connection_timeout,
            create_database,
            min_connections,
            max_connections,
            evictor_tests_per_run,
            test_while_idle,
            max_connection_idle_time,
            loose_bbox,
        )

        r = None
        try:
            if overwrite:
                url = "{}/rest/workspaces/{}/datastores/{}".format(
                    self.service_url, workspace, store_name
                )

                r = self._requests(
                    "put",
                    url,
                    data=database_connection,
                    headers=headers,
                )

                if r.status_code not in [200, 201]:
                    return "{}: Datastore can not be updated. {}".format(
                        r.status_code, r.content
                    )
            else:
                r = self._requests(
                    "post",
                    url,
                    data=database_connection,
                    headers=headers,
                )

                if r.status_code not in [200, 201]:
                    return "{}: Data store can not be created! {}".format(
                        r.status_code, r.content
                    )

        except Exception as e:
            return "Error: {}".format(e)