"""
Unit tests for resdk/resolwe.py file.
"""


import os
import unittest

import requests
from mock import MagicMock, patch
from slumber.exceptions import SlumberHttpBaseException

from resdk.exceptions import ResolweServerError, ValidationError
from resdk.resolwe import ResAuth, Resolwe, ResolweResource
from resdk.resources import Collection, Data, Process

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestResolweResource(unittest.TestCase):
    def setUp(self):
        self.resource = ResolweResource()
        self.method_mock = MagicMock(
            side_effect=[42, SlumberHttpBaseException(content="error mesage")]
        )

    def test_get_wrapped(self):
        self.resource.get = self.method_mock
        self.assertEqual(self.resource.get(), 42)

        with self.assertRaises(ResolweServerError):
            self.resource.get()

    def test_options_wrapped(self):
        self.resource.options = self.method_mock
        self.assertEqual(self.resource.options(), 42)

        with self.assertRaises(ResolweServerError):
            self.resource.options()

    def test_head_wrapped(self):
        self.resource.head = self.method_mock
        self.assertEqual(self.resource.head(), 42)

        with self.assertRaises(ResolweServerError):
            self.resource.head()

    def test_post_wrapped(self):
        self.resource.post = self.method_mock
        self.assertEqual(self.resource.post(), 42)

        with self.assertRaises(ResolweServerError):
            self.resource.post()

    def test_patch_wrapped(self):
        self.resource.patch = self.method_mock
        self.assertEqual(self.resource.patch(), 42)

        with self.assertRaises(ResolweServerError):
            self.resource.patch()

    def test_put_wrapped(self):
        self.resource.put = self.method_mock
        self.assertEqual(self.resource.put(), 42)

        with self.assertRaises(ResolweServerError):
            self.resource.put()

    def test_delete_wrapped(self):
        self.resource.delete = self.method_mock
        self.assertEqual(self.resource.delete(), 42)

        with self.assertRaises(ResolweServerError):
            self.resource.delete()


class TestResolwe(unittest.TestCase):
    @patch("resdk.resolwe.logging")
    @patch("resdk.resolwe.ResolweAPI")
    @patch("resdk.resolwe.slumber")
    @patch("resdk.resolwe.ResAuth")
    @patch("resdk.resolwe.Resolwe", spec=Resolwe)
    def test_init(
        self, resolwe_mock, resauth_mock, slumber_mock, resolwe_api_mock, log_mock
    ):
        Resolwe.__init__(resolwe_mock, "a", "b", "http://some/url")
        self.assertEqual(log_mock.getLogger.call_count, 1)

    def test_validate_url(self):
        resolwe = MagicMock(spec=Resolwe)

        message = "Server url must start with .*"
        with self.assertRaisesRegex(ValueError, message):
            Resolwe._validate_url(resolwe, "starts.without.http")

        resolwe.session = MagicMock(
            get=MagicMock(side_effect=requests.exceptions.ConnectionError())
        )
        message = "The site can't be reached: .*"
        with self.assertRaisesRegex(ValueError, message):
            Resolwe._validate_url(resolwe, "http://invalid.url")

    @patch("resdk.resolwe.ResolweAPI")
    @patch("resdk.resolwe.ResAuth")
    @patch("resdk.resolwe.Resolwe", spec=Resolwe)
    def test_login(self, resolwe_mock, resauth_mock, resolwe_api_mock):
        resolwe_mock.url = "http://some/url"
        resauth_mock.cookies = {}
        Resolwe._login(resolwe_mock, "a", "b")
        self.assertEqual(resauth_mock.call_count, 1)
        self.assertEqual(resolwe_api_mock.call_count, 1)

    def test_repr(self):
        resolwe_mock = MagicMock(spec=Resolwe, url="www.abc.com")

        resolwe_mock.auth = MagicMock(username="user")
        rep = Resolwe.__repr__(resolwe_mock)
        self.assertEqual(rep, "Resolwe <url: www.abc.com, username: user>")

        resolwe_mock.auth = MagicMock(username=None)
        rep = Resolwe.__repr__(resolwe_mock)
        self.assertEqual(rep, "Resolwe <url: www.abc.com>")

    @patch("resdk.resolwe.requests")
    @patch("resdk.resolwe.ResAuth")
    def test_env_variables(self, resauth_mock, requests_mock):
        # Ensure environmental variables are not set.
        os.environ.pop("RESOLWE_HOST_URL", None)
        os.environ.pop("RESOLWE_API_USERNAME", None)
        os.environ.pop("RESOLWE_API_PASSWORD", None)

        # Default URL should be used by default.
        resolwe_api = Resolwe()
        self.assertEqual(resolwe_api.url, "http://localhost:8000")
        self.assertEqual(resauth_mock.call_args[0][0], None)
        self.assertEqual(resauth_mock.call_args[0][1], None)

        # If environment variable is set, it overrides the default URL.
        os.environ["RESOLWE_API_USERNAME"] = "foo"
        os.environ["RESOLWE_API_PASSWORD"] = "bar"
        os.environ["RESOLWE_HOST_URL"] = "http://resolwe-api:8000"
        resolwe_api = Resolwe()
        self.assertEqual(resolwe_api.url, "http://resolwe-api:8000")
        self.assertEqual(resauth_mock.call_args[0][0], "foo")
        self.assertEqual(resauth_mock.call_args[0][1], "bar")


class TestProcessFileField(unittest.TestCase):
    @patch("resdk.resolwe.os", autospec=True)
    @patch("resdk.resolwe.Resolwe", autospec=True)
    def test_invalid_file_name(self, resolwe_mock, os_mock):
        os_mock.configure_mock(**{"path.isfile.return_value": False})

        message = r"File .* not found."
        with self.assertRaisesRegex(ValueError, message):
            Resolwe._process_file_field(resolwe_mock, "/bad/path/to/file")
        self.assertEqual(resolwe_mock._upload_file.call_count, 0)

    @patch("resdk.resolwe.os")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_if_upload_fails(self, resolwe_mock, os_mock):
        # Good file, upload fails
        os_mock.configure_mock(**{"path.isfile.return_value": True})
        resolwe_mock._upload_file = MagicMock(return_value=None)

        message = r"Upload failed for .*"
        with self.assertRaisesRegex(Exception, message):
            Resolwe._process_file_field(resolwe_mock, "/good/path/to/file")
        self.assertEqual(resolwe_mock._upload_file.call_count, 1)

    @patch("resdk.resolwe.ntpath")
    @patch("resdk.resolwe.os")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_if_upload_ok(self, resolwe_mock, os_mock, ntpath_mock):
        # Good file, upload fails
        os_mock.configure_mock(**{"path.isfile.return_value": True})
        resolwe_mock._upload_file = MagicMock(return_value="temporary_file")
        ntpath_mock.basename.return_value = "Basename returned!"

        output = Resolwe._process_file_field(resolwe_mock, "/good/path/to/file.txt")
        self.assertEqual(
            output, {"file": "Basename returned!", "file_temp": "temporary_file"}
        )

        resolwe_mock._upload_file.assert_called_once_with("/good/path/to/file.txt")

    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_url(self, resolwe_mock):
        output = Resolwe._process_file_field(
            resolwe_mock, "http://www.example.com/reads.fq.gz"
        )
        self.assertEqual(
            output,
            {"file": "reads.fq.gz", "file_temp": "http://www.example.com/reads.fq.gz"},
        )


class TestRun(unittest.TestCase):
    def setUp(self):
        self.process_mock = MagicMock(spec=Process)
        self.process_mock.slug = "some:prc:slug:"
        self.process_mock.input_schema = [
            {
                "label": "NGS reads (FASTQ)",
                "type": "basic:file:",
                "required": "false",
                "name": "src",
            },
            {
                "label": "list of NGS reads",
                "type": "list:basic:file:",
                "required": "false",
                "name": "src_list",
            },
            {
                "label": "Genome object",
                "type": "data:genome:fasta:",
                "required": "false",
                "name": "genome",
            },
            {
                "label": "List of reads objects",
                "type": "list:data:reads:fastg:",
                "required": "false",
                "name": "reads",
            },
        ]

    @patch("resdk.resolwe.Data")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_run_process(self, resolwe_mock, data_mock):
        resolwe_mock.api = MagicMock(**{"process.get.return_value": self.process_mock})

        Resolwe.run(resolwe_mock)
        self.assertEqual(resolwe_mock.api.data.post.call_count, 1)

    @patch("resdk.resolwe.Data")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_get_or_run(self, resolwe_mock, data_mock):
        resolwe_mock.api = MagicMock(**{"process.get.return_value": self.process_mock})

        Resolwe.get_or_run(resolwe_mock)
        self.assertEqual(resolwe_mock.api.data.get_or_create.post.call_count, 1)

    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_wrap_list(self, resolwe_mock):
        process = self.process_mock

        Resolwe._process_inputs(resolwe_mock, {"src_list": ["/path/to/file"]}, process)
        resolwe_mock._process_file_field.assert_called_once_with("/path/to/file")

        resolwe_mock.reset_mock()
        Resolwe._process_inputs(resolwe_mock, {"src_list": "/path/to/file"}, process)
        resolwe_mock._process_file_field.assert_called_once_with("/path/to/file")

    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_keep_input(self, resolwe_mock):
        process = self.process_mock

        input_dict = {"src_list": ["/path/to/file"]}
        Resolwe._process_inputs(resolwe_mock, input_dict, process)
        self.assertEqual(input_dict, {"src_list": ["/path/to/file"]})

    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_bad_descriptor_input(self, resolwe_mock):
        # Raise error is only one of deswcriptor/descriptor_schema is given:
        message = "Set both or neither descriptor and descriptor_schema."
        with self.assertRaisesRegex(ValueError, message):
            Resolwe.run(resolwe_mock, descriptor="a")
        with self.assertRaisesRegex(ValueError, message):
            Resolwe.run(resolwe_mock, descriptor_schema="a")

    @patch("resdk.resolwe.os")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_bad_inputs(self, resolwe_mock, os_mock):
        # Good file, upload fails becouse of bad input keyword
        os_mock.path.isfile.return_value = True
        process = self.process_mock

        resolwe_mock._upload_file = MagicMock(return_value=None)
        message = r"Field .* not in process .* input schema."
        with self.assertRaisesRegex(ValidationError, message):
            Resolwe._process_inputs(
                resolwe_mock, {"bad_key": "/good/path/to/file"}, process
            )

    @patch("resdk.resolwe.Data")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_file_processing(self, resolwe_mock, data_mock):

        resolwe_mock.api = MagicMock(
            **{
                "process.get.return_value": self.process_mock,
                "data.post.return_value": {},
            }
        )
        resolwe_mock._process_file_field = MagicMock(
            side_effect=[
                {"file": "file_name1", "file_temp": "temp_file1"},
                {"file": "file_name2", "file_temp": "temp_file2"},
                {"file": "file_name3", "file_temp": "temp_file3"},
            ]
        )
        data_mock.return_value = "Data object"

        Resolwe.run(
            resolwe_mock,
            input={
                "src": "/path/to/file1",
                "src_list": ["/path/to/file2", "/path/to/file3"],
            },
        )

    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_dehydrate_data(self, resolwe_mock):
        data_obj = Data(id=1, resolwe=MagicMock())
        data_obj.id = 1  # this is overriden when initialized
        process = self.process_mock

        result = Resolwe._process_inputs(resolwe_mock, {"genome": data_obj}, process)
        self.assertEqual(result, {"genome": 1})

        result = Resolwe._process_inputs(resolwe_mock, {"reads": [data_obj]}, process)
        self.assertEqual(result, {"reads": [1]})

    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_dehydrate_collection(self, resolwe_mock):
        resolwe_mock._get_process.return_value = Process(
            resolwe=MagicMock(), slug="process-slug"
        )
        resolwe_mock._process_inputs.return_value = {}
        resolwe_mock.api = MagicMock(**{"data.post.return_value": {}})

        Resolwe.run(
            self=resolwe_mock,
            slug="process-slug",
            collection=Collection(id=1, resolwe=MagicMock()),
        )
        resolwe_mock.api.data.post.assert_called_once_with(
            {
                "process": {"slug": "process-slug"},
                "input": {},
                "collection": {"id": 1},
            }
        )

    @patch("resdk.resolwe.Data")
    @patch("resdk.resolwe.os")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_call_with_all_args(self, resolwe_mock, os_mock, data_mock):
        resolwe_mock.api = MagicMock(
            **{
                "process.get.return_value": self.process_mock,
                "data.post.return_value": {"data": "some_data"},
            }
        )
        data_mock.return_value = "Data object"

        data = Resolwe.run(
            resolwe_mock,
            data_name="some_name",
            descriptor="descriptor",
            descriptor_schema="descriptor_schema",
            collection=1,
        )
        # Confirm that no files to upload in input:
        self.assertEqual(resolwe_mock._upload_file.call_count, 0)
        data_mock.assert_called_with(data="some_data", resolwe=resolwe_mock)
        self.assertEqual(data, "Data object")


class TestUploadFile(unittest.TestCase):
    def setUp(self):
        self.file_path = os.path.join(BASE_DIR, "files", "example.fastq")
        self.config = {
            "url": "http://some/url",
            "auth": MagicMock(),
            "logger": MagicMock(),
        }

    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_always_ok(self, resolwe_mock):
        resolwe_mock.configure_mock(**self.config)
        # Immitate response form server - always status 200:
        requests_response = {"files": [{"temp": "fake_name"}]}
        resolwe_mock.session.post.return_value = MagicMock(
            status_code=200, **{"json.return_value": requests_response}
        )

        response = Resolwe._upload_file(resolwe_mock, self.file_path)

        self.assertEqual(response, "fake_name")

    @patch("resdk.resolwe.requests")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_always_bad(self, resolwe_mock, requests_mock):
        resolwe_mock.configure_mock(**self.config)
        # Immitate response form server - always status 400
        requests_mock.post.return_value = MagicMock(status_code=400)

        response = Resolwe._upload_file(resolwe_mock, self.file_path)

        self.assertIsNone(response)
        self.assertEqual(resolwe_mock.logger.warning.call_count, 4)

    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_one_bad_other_ok(self, resolwe_mock):
        resolwe_mock.configure_mock(**self.config)
        requests_response = {"files": [{"temp": "fake_name"}]}
        response_ok = MagicMock(
            status_code=200, **{"json.return_value": requests_response}
        )
        response_fails = MagicMock(status_code=400)
        # Immitate response form server - one status 400, but other 200:
        resolwe_mock.session.post.side_effect = [
            response_fails,
            response_ok,
            response_ok,
        ]
        response = Resolwe._upload_file(resolwe_mock, self.file_path)

        self.assertEqual(response, "fake_name")
        self.assertEqual(resolwe_mock.logger.warning.call_count, 1)


class TestDownload(unittest.TestCase):
    def setUp(self):
        self.file_list = ["/the/first/file.txt", "/the/second/file.py"]
        self.config = {
            "url": "http://some/url",
            "auth": MagicMock(),
            "logger": MagicMock(),
        }

    @patch("resdk.resolwe.os")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_fail_if_bad_dir(self, resolwe_mock, os_mock):
        resolwe_mock.configure_mock(**self.config)
        os_mock.path.isdir.return_value = False

        message = "Download directory does not exist: .*"
        with self.assertRaisesRegex(ValueError, message):
            Resolwe._download_files(resolwe_mock, self.file_list)

    @patch("resdk.resolwe.os")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_empty_file_list(self, resolwe_mock, os_mock):
        resolwe_mock.configure_mock(**self.config)

        Resolwe._download_files(resolwe_mock, [])

        resolwe_mock.logger.info.assert_called_once_with("No files to download.")

    @patch("resdk.resolwe.os")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_bad_response(self, resolwe_mock, os_mock):
        resolwe_mock.configure_mock(**self.config)
        os_mock.path.isfile.return_value = True
        response = {"raise_for_status.side_effect": Exception("abc")}
        resolwe_mock.session.get.return_value = MagicMock(ok=False, **response)

        with self.assertRaisesRegex(Exception, "abc"):
            Resolwe._download_files(resolwe_mock, self.file_list[:1])
        self.assertEqual(resolwe_mock.logger.info.call_count, 2)

    @patch("resdk.resolwe.open")
    @patch("resdk.resolwe.os")
    @patch("resdk.resolwe.Resolwe", spec=True)
    def test_good_response(self, resolwe_mock, os_mock, open_mock):
        resolwe_mock.configure_mock(**self.config)
        os_mock.path.isfile.return_value = True

        resolwe_mock.session.get.return_value = MagicMock(
            ok=True, **{"iter_content.return_value": range(3)}
        )

        Resolwe._download_files(resolwe_mock, self.file_list)
        self.assertEqual(resolwe_mock.logger.info.call_count, 3)

        # This asserts may seem wierd. To check what is happening behind the scenes:
        # print(open_mock.mock_calls)
        self.assertEqual(
            open_mock.return_value.__enter__.return_value.write.call_count, 6
        )
        # Why 6? 2 files in self.file_list, each downloads 3 chunks (defined in response mock)


class TestResAuth(unittest.TestCase):
    @patch("resdk.resolwe.ResAuth", spec=True)
    def setUp(self, auth_mock):
        auth_mock.configure_mock(sessionid=None, csrftoken=None)
        self.auth_mock = auth_mock

    @patch("resdk.resolwe.requests.post")
    def test_bad_url(self, requests_post_mock):
        requests_post_mock.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaisesRegex(
            ValueError, "Server not accessible on www.abc.com. Wrong url?"
        ):
            ResAuth.__init__(
                self.auth_mock, username="usr", password="pwd", url="www.abc.com"
            )

    @patch("resdk.resolwe.requests")
    def test_bad_credentials(self, requests_mock):
        requests_mock.post = MagicMock(return_value=MagicMock(status_code=400))

        message = r"Response HTTP status code .* Invalid credentials?"
        with self.assertRaisesRegex(ValueError, message):
            ResAuth.__init__(
                self.auth_mock, username="usr", password="pwd", url="www.abc.com"
            )

    @patch("resdk.resolwe.requests")
    def test_no_csrf_token(self, requests_mock):
        post_mock = MagicMock(status_code=200, cookies={"sessionid": 42})
        requests_mock.post = MagicMock(return_value=post_mock)

        message = "Missing sessionid or csrftoken. Invalid credentials?"
        with self.assertRaisesRegex(Exception, message):
            ResAuth.__init__(
                self.auth_mock, username="usr", password="pwd", url="www.abc.com"
            )

    @patch("resdk.resolwe.requests")
    def test_all_ok(self, requests_mock):
        post_mock = MagicMock(
            status_code=200, cookies={"sessionid": 42, "csrftoken": 43}
        )
        requests_mock.post = MagicMock(return_value=post_mock)

        ResAuth.__init__(
            self.auth_mock, username="usr", password="pwd", url="www.abc.com"
        )
        self.assertEqual(self.auth_mock.sessionid, 42)
        self.assertEqual(self.auth_mock.csrftoken, 43)

    @patch("resdk.resolwe.requests")
    def test_public_user(self, requests_mock):
        post_mock = MagicMock(status_code=200)
        requests_mock.post = MagicMock(return_value=post_mock)

        ResAuth.__init__(self.auth_mock, url="www.abc.com")
        self.assertEqual(self.auth_mock.sessionid, None)
        self.assertEqual(self.auth_mock.csrftoken, None)

    def test_call(self):
        res_auth = MagicMock(
            spec=ResAuth, sessionid=None, csrftoken=None, url="www.abc.com"
        )
        resp = ResAuth.__call__(res_auth, MagicMock(headers={}))
        self.assertDictEqual(resp.headers, {"referer": "www.abc.com"})

        res_auth = MagicMock(
            spec=ResAuth, sessionid="my-id", csrftoken="my-token", url="abc.com"
        )
        resp = ResAuth.__call__(res_auth, MagicMock(headers={}))
        self.assertDictEqual(
            resp.headers,
            {"X-CSRFToken": "my-token", "referer": "abc.com"},
        )


if __name__ == "__main__":
    unittest.main()
