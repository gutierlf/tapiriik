import collections
ResponseWithoutJson = collections.namedtuple('ResponseWithoutJson', 'status_code')

class ResponseWithJson(object):
    status_code = 200

    def __init__(self, json=None):
       self._json = json

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
