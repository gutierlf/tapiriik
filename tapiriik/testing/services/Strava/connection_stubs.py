import collections
import json
import os

ResponseWithoutJson = collections.namedtuple('ResponseWithoutJson', 'status_code')

class ResponseWithJson(object):
    status_code = 200

    def __init__(self, the_json=None):
       self._json = the_json

    def json(self):
        return self._json

HTTP_FOUR_OH_ONE_RESPONSE              = ResponseWithoutJson(status_code=401)
HTTP_NO_JSON_RESPONSE                  = ResponseWithoutJson(status_code=200)
HTTP_RECORD_NOT_FOUND_RESPONSE         = ResponseWithJson({"message": "Record Not Found"})
HTTP_ERROR_IN_DOWNLOADED_DATA_RESPONSE = ResponseWithJson([{"type": "error", "data": "the error message"}])

class Http401Getter(object):
    @staticmethod
    def getActivity(*_):
        return HTTP_FOUR_OH_ONE_RESPONSE

class HttpNoJsonGetter(object):
    @staticmethod
    def getActivity(*_):
        return HTTP_NO_JSON_RESPONSE

class HttpRecordNotFoundGetter(object):
    @staticmethod
    def getActivity(*_):
        return HTTP_RECORD_NOT_FOUND_RESPONSE

class HttpErrorInDownloadedDataGetter(object):
    @staticmethod
    def getActivity(*_):
        return HTTP_ERROR_IN_DOWNLOADED_DATA_RESPONSE

class FileLoader(object):
    @staticmethod
    def getActivity(activityID, _):
        filename = os.path.join(os.path.dirname(__file__),
                                'test_data', str(activityID) + ".strava")
        with open(filename, "r") as the_file:
            text = the_file.read()
        return ResponseWithJson(json.loads(text))
