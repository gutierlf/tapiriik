import collections
Response = collections.namedtuple('Response', 'status_code')

class Http401Returner(object):
    @staticmethod
    def getActivity(activityID, headers):
        return Response(status_code=401)

class HttpNoJsonReturner(object):
    @staticmethod
    def getActivity(activityID, headers):
        return Response(status_code=200)
