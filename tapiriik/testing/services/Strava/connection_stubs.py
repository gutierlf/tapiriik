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

class Http401Getter(object):
    @staticmethod
    def getActivity(activityID, headers):
        return ResponseWithoutJson(status_code=401)

class HttpNoJsonGetter(object):
    @staticmethod
    def getActivity(activityID, headers):
        return ResponseWithoutJson(status_code=200)

class HttpRecordNotFoundGetter(object):
    @staticmethod
    def getActivity(activityID, headers):
        return ResponseWithJson({"message": "Record Not Found"})

class HttpErrorInDownloadedDataGetter(object):
    @staticmethod
    def getActivity(activityID, headers):
        return ResponseWithJson([{"type": "error", "data": "the error message"}])

class FileLoader(object):
    @staticmethod
    def getActivity(activityID, _):
        filename = os.path.join(os.path.dirname(__file__),
                                'test_data', str(activityID) + ".strava")
        with open(filename, "r") as the_file:
            text = the_file.read()
        return ResponseWithJson(json.loads(text))
