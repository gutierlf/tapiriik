import collections
ResponseWithoutJson = collections.namedtuple('ResponseWithoutJson', 'status_code')

class ResponseWithJson(object):
    status_code = 200

    def __init__(self, json=None):
       self._json = json

    def json(self):
        return self._json

class Http401Returner(object):
    @staticmethod
    def getActivity(activityID, headers):
        return ResponseWithoutJson(status_code=401)

class HttpNoJsonReturner(object):
    @staticmethod
    def getActivity(activityID, headers):
        return ResponseWithoutJson(status_code=200)

class HttpRecordNotFoundReturner(object):
    @staticmethod
    def getActivity(activityID, headers):
        return ResponseWithJson({"message": "Record Not Found"})
