class Http401Returner(object):
    @staticmethod
    def getActivity(activityID, headers):
        class StatusCode401(object):
            status_code = 401
        return StatusCode401()
