""".. Ignore pydocstyle D400.

=======
Resolwe
=======

.. autoclass:: resdk.Resolwe
   :members:

"""
import getpass
import logging
import ntpath
import os
import re
import uuid
from urllib.parse import urljoin

import requests
import slumber

from .constants import CHUNK_SIZE
from .exceptions import ValidationError, handle_http_exception
from .query import ResolweQuery
from .resources import (
    Collection,
    Data,
    DescriptorSchema,
    Group,
    Process,
    Relation,
    Sample,
    User,
)
from .resources.base import BaseResource
from .resources.kb import Feature, Mapping
from .resources.utils import get_collection_id, get_data_id, is_data, iterate_fields
from .utils import is_email

DEFAULT_URL = "http://localhost:8000"


class ResolweResource(slumber.Resource):
    """Wrapper around slumber's Resource with custom exceptions handler."""

    def __getattribute__(self, item):
        """Return class attribute and wrapp request methods in exception handler."""
        attr = super().__getattribute__(item)
        if item in ["get", "options", "head", "post", "patch", "put", "delete"]:
            return handle_http_exception(attr)
        return attr


class ResolweAPI(slumber.API):
    """Use custom ResolweResource resource class in slumber's API."""

    resource_class = ResolweResource


class Resolwe:
    """Connect to a Resolwe server.

    :param username: user's username
    :type username: str
    :param password: user's password
    :type password: str
    :param url: Resolwe server instance
    :type url: str

    """

    # Map resource class to ResolweQuery name
    resource_query_mapping = {
        Data: "data",
        Collection: "collection",
        Sample: "sample",
        Relation: "relation",
        Process: "process",
        DescriptorSchema: "descriptor_schema",
        User: "user",
        Group: "group",
        Feature: "feature",
        Mapping: "mapping",
    }
    # Map ResolweQuery name to it's slug_field
    slug_field_mapping = {
        "user": "username",
        "group": "name",
    }

    data = None
    collection = None
    sample = None
    relation = None
    process = None
    descriptor_schema = None
    user = None
    group = None
    feature = None
    mapping = None

    session = None

    def __init__(self, username=None, password=None, url=None):
        """Initialize attributes."""
        self.session = requests.Session()
        if url is None:
            # Try to get URL from environmental variable, otherwise fallback to default.
            url = os.environ.get("RESOLWE_HOST_URL", DEFAULT_URL)

        self._validate_url(url)

        if username is None:
            username = os.environ.get("RESOLWE_API_USERNAME", None)

        if password is None:
            password = os.environ.get("RESOLWE_API_PASSWORD", None)

        self.url = url
        self._login(username=username, password=password)

        self.logger = logging.getLogger(__name__)

    def _validate_url(self, url):
        if not re.match(r"https?://", url):
            raise ValueError("Server url must start with http(s)://")

        try:
            self.session.get(urljoin(url, "/api/"))
        except requests.exceptions.ConnectionError:
            raise ValueError("The site can't be reached: {}".format(url))

    def _initialize_queries(self):
        """Initialize ResolweQuery's."""
        for resource, query_name in self.resource_query_mapping.items():
            slug_field = self.slug_field_mapping.get(query_name, "slug")
            setattr(
                self, query_name, ResolweQuery(self, resource, slug_field=slug_field)
            )

    def _login(self, username=None, password=None):
        self.auth = ResAuth(username, password, self.url)
        self.session.cookies = requests.utils.cookiejar_from_dict(self.auth.cookies)
        self.api = ResolweAPI(
            urljoin(self.url, "/api/"),
            self.auth,
            session=self.session,
            append_slash=False,
        )
        self._initialize_queries()

    def login(self, username=None, password=None):
        """Interactive login.

        Ask the user to enter credentials in command prompt. If
        username / email and password are given, login without prompt.
        """
        if username is None:
            username = input("Username (or email): ")
        if password is None:
            password = getpass.getpass("Password: ")
        self._login(username=username, password=password)

    def get_query_by_resource(self, resource):
        """Get ResolweQuery for a given resource."""
        if isinstance(resource, BaseResource):
            resource = resource.__class__
        elif not issubclass(resource, BaseResource):
            raise ValueError(
                "Provide a Resource class or it's instance as a resource argument."
            )

        return getattr(self, self.resource_query_mapping.get(resource))

    def __repr__(self):
        """Return string representation of the current object."""
        if self.auth.username:
            return "Resolwe <url: {}, username: {}>".format(
                self.url, self.auth.username
            )
        return "Resolwe <url: {}>".format(self.url)

    def _process_file_field(self, path):
        """Process file field and return it in resolwe-specific format.

        Upload referenced file if it is stored locally and return
        original filename and it's temporary location.

        :param path: path to file (local or url)
        :type path: str/path

        :rtype: dict
        """
        if isinstance(path, dict) and "file" in path and "file_temp" in path:
            return path

        url_regex = (
            r"^(https?|ftp)://[-A-Za-z0-9\+&@#/%?=~_|!:,.;]*[-A-Za-z0-9\+&@#/%=~_|]$"
        )
        if re.match(url_regex, path):
            file_name = path.split("/")[-1].split("#")[0].split("?")[0]
            return {"file": file_name, "file_temp": path}

        if not os.path.isfile(path):
            raise ValueError("File {} not found.".format(path))

        file_temp = self._upload_file(path)

        if not file_temp:
            raise Exception("Upload failed for {}.".format(path))

        file_name = ntpath.basename(path)
        return {
            "file": file_name,
            "file_temp": file_temp,
        }

    def _get_process(self, slug=None):
        """Return process with given slug.

        Raise error if process doesn't exist or more than one is returned.
        """
        return self.process.get(slug=slug)

    def _process_inputs(self, inputs, process):
        """Process input fields.

        Processing includes:
        * wrapping ``list:*`` to the list if they are not already
        * dehydrating values of ``data:*`` and ``list:data:*`` fields
        * uploading files in ``basic:file:`` and ``list:basic:file:``
          fields
        """

        def deep_copy(current):
            """Copy inputs."""
            if isinstance(current, dict):
                return {key: deep_copy(val) for key, val in current.items()}
            elif isinstance(current, list):
                return [deep_copy(val) for val in current]
            elif is_data(current):
                return current.id
            else:
                return current

        # leave original intact
        inputs = deep_copy(inputs)

        try:
            for schema, fields in iterate_fields(inputs, process.input_schema):
                field_name = schema["name"]
                field_type = schema["type"]
                field_value = fields[field_name]

                # XXX: Remove this when supported on server.
                # Wrap `list:` fields into list if they are not already
                if field_type.startswith("list:") and not isinstance(field_value, list):
                    fields[field_name] = [field_value]
                    field_value = fields[
                        field_name
                    ]  # update value for the rest of the loop

                # Dehydrate `data:*` fields
                if field_type.startswith("data:"):
                    fields[field_name] = get_data_id(field_value)

                # Dehydrate `list:data:*` fields
                elif field_type.startswith("list:data:"):
                    fields[field_name] = [get_data_id(data) for data in field_value]

                # Upload files in `basic:file:` fields
                elif field_type == "basic:file:":
                    fields[field_name] = self._process_file_field(field_value)

                # Upload files in list:basic:file:` fields
                elif field_type == "list:basic:file:":
                    fields[field_name] = [
                        self._process_file_field(obj) for obj in field_value
                    ]

        except KeyError as key_error:
            field_name = key_error.args[0]
            slug = process.slug
            raise ValidationError(
                "Field '{}' not in process '{}' input schema.".format(field_name, slug)
            )

        return inputs

    def run(
        self,
        slug=None,
        input={},
        descriptor=None,
        descriptor_schema=None,
        collection=None,
        data_name="",
    ):
        """Run process and return the corresponding Data object.

        1. Upload files referenced in inputs
        2. Create Data object with given inputs
        3. Command is run that processes inputs into outputs
        4. Return Data object

        The processing runs asynchronously, so the returned Data
        object does not have an OK status or outputs when returned.
        Use data.update() to refresh the Data resource object.

        :param str slug: Process slug (human readable unique identifier)
        :param dict input: Input values
        :param dict descriptor: Descriptor values
        :param str descriptor_schema: A valid descriptor schema slug
        :param int/resource collection: Collection resource or it's id
            into which data object should be included
        :param str data_name: Default name of data object

        :return: data object that was just created
        :rtype: Data object
        """
        if (descriptor and not descriptor_schema) or (
            not descriptor and descriptor_schema
        ):
            raise ValueError("Set both or neither descriptor and descriptor_schema.")

        process = self._get_process(slug)
        data = {
            "process": {"slug": process.slug},
            "input": self._process_inputs(input, process),
        }

        if descriptor and descriptor_schema:
            data["descriptor"] = descriptor
            data["descriptor_schema"] = {"slug": descriptor_schema}

        if collection:
            data["collection"] = {"id": get_collection_id(collection)}

        if data_name:
            data["name"] = data_name

        model_data = self.api.data.post(data)
        return Data(resolwe=self, **model_data)

    def get_or_run(self, slug=None, input={}):
        """Return existing object if found, otherwise create new one.

        :param str slug: Process slug (human readable unique identifier)
        :param dict input: Input values
        """
        process = self._get_process(slug)
        inputs = self._process_inputs(input, process)

        data = {
            "process": process.slug,
            "input": inputs,
        }

        model_data = self.api.data.get_or_create.post(data)
        return Data(resolwe=self, **model_data)

    def _upload_file(self, file_path):
        """Upload a single file to the server.

        File is uploaded in chunks of size CHUNK_SIZE bytes.

        :param str file_path: File path

        """
        response = None
        chunk_number = 0
        session_id = str(uuid.uuid4())
        file_uid = str(uuid.uuid4())
        file_size = os.path.getsize(file_path)
        base_name = os.path.basename(file_path)

        with open(file_path, "rb") as file_:
            while True:
                chunk = file_.read(CHUNK_SIZE)
                if not chunk:
                    break

                for i in range(5):
                    if i > 0 and response is not None:
                        self.logger.warning(
                            "Chunk upload failed (error %s): repeating for chunk number %s",
                            response.status_code,
                            chunk_number,
                        )

                    response = self.session.post(
                        urljoin(self.url, "upload/"),
                        auth=self.auth,
                        # request are smart and make
                        # 'CONTENT_TYPE': 'multipart/form-data;''
                        files={"file": (base_name, chunk)},
                        # stuff in data will be in response.POST on server
                        data={
                            "_chunkSize": CHUNK_SIZE,
                            "_totalSize": file_size,
                            "_chunkNumber": chunk_number,
                            "_currentChunkSize": len(chunk),
                        },
                        headers={"Session-Id": session_id, "X-File-Uid": file_uid},
                    )

                    if response.status_code in [200, 201]:
                        break
                else:
                    # Upload of a chunk failed (5 retries)
                    return None

                progress = 100.0 * (chunk_number * CHUNK_SIZE + len(chunk)) / file_size
                message = "{:.0f} % Uploaded {}".format(progress, file_path)
                self.logger.info(message)
                chunk_number += 1

        return response.json()["files"][0]["temp"]

    def _download_files(self, files, download_dir=None):
        """Download files.

        Download files from the Resolwe server to the download
        directory (defaults to the current working directory).

        :param files: files to download
        :type files: list of file URI
        :param download_dir: download directory
        :type download_dir: string
        :rtype: None

        """
        if not download_dir:
            download_dir = os.getcwd()

        if not os.path.isdir(download_dir):
            raise ValueError(
                "Download directory does not exist: {}".format(download_dir)
            )

        if not files:
            self.logger.info("No files to download.")

        else:
            self.logger.info("Downloading files to %s:", download_dir)

            for file_uri in files:
                file_name = os.path.basename(file_uri)
                file_path = os.path.dirname(file_uri)
                file_url = urljoin(self.url, "data/{}".format(file_uri))

                # Remove data id from path
                file_path = file_path.split("/", 1)[1] if "/" in file_path else ""
                full_path = os.path.join(download_dir, file_path)
                if not os.path.isdir(full_path):
                    os.makedirs(full_path)

                self.logger.info("* %s", os.path.join(file_path, file_name))

                with open(
                    os.path.join(download_dir, file_path, file_name), "wb"
                ) as file_handle:
                    response = self.session.get(file_url, stream=True, auth=self.auth)

                    if not response.ok:
                        response.raise_for_status()
                    else:
                        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                            file_handle.write(chunk)

    def data_usage(self, **query_params):
        """Get per-user data usage information.

        Display number of samples, data objects and sum of data object
        sizes for currently logged-in user. For admin users, display
        data for **all** users.
        """
        return self.api.base.data_usage.get(**query_params)


class ResAuth(requests.auth.AuthBase):
    """HTTP Resolwe Authentication for Request object.

    :param str username: user's username
    :param str password: user's password
    :param str url: Resolwe server address

    """

    #: Session ID used in HTTP requests
    sessionid = None
    #: CSRF token used in HTTP requests
    csrftoken = None

    def __init__(self, username=None, password=None, url=DEFAULT_URL):
        """Authenticate user on Resolwe server."""
        self.logger = logging.getLogger(__name__)
        self.cookies = {}

        self.username = username
        self.url = url

        if not username and not password:
            return

        key = "email" if is_email(username) else "username"
        payload = {key: username, "password": password}

        try:
            response = requests.post(urljoin(url, "/rest-auth/login/"), data=payload)
        except requests.exceptions.ConnectionError:
            raise ValueError("Server not accessible on {}. Wrong url?".format(url))

        status_code = response.status_code
        if status_code in [400, 403]:
            msg = "Response HTTP status code {}. Invalid credentials?".format(
                status_code
            )
            raise ValueError(msg)

        if not ("sessionid" in response.cookies and "csrftoken" in response.cookies):
            raise Exception("Missing sessionid or csrftoken. Invalid credentials?")

        self.sessionid = response.cookies["sessionid"]
        self.csrftoken = response.cookies["csrftoken"]
        self.url = url
        self.cookies = {"csrftoken": self.csrftoken, "sessionid": self.sessionid}

    def __call__(self, request):
        """Set request headers."""
        if self.sessionid and self.csrftoken:
            request.headers["X-CSRFToken"] = self.csrftoken

        request.headers["referer"] = self.url

        # Not needed until we support HTTP Push with the API
        # if r.path_url != '/upload/':
        #     r.headers['X-SubscribeID'] = self.subscribe_id
        return request
