from tapiriik.testing.testtools import TapiriikTestCase, TestTools
from tapiriik.testing.services.http_stubs import Http401Returner

from tapiriik.services.Strava import StravaService
from tapiriik.services.api import APIException

class StravaServiceTests(TapiriikTestCase):
    def testStatusCode401RaisesAPIException(self):
        svc = TestTools.create_mock_service("Strava")
        svcRecord = TestTools.create_mock_svc_record(svc)
        svcRecord.Authorization = {"OAuthToken": "token"}
        activity = TestTools.create_blank_activity(record=svcRecord)
        activity.ServiceData = {"Manual": False, "ActivityID": 1}

        with self.assertRaises(APIException) as cm:
            StravaService().DownloadActivity(svcRecord, activity, http_getter=Http401Returner)
        self.assertEqual(cm.exception.Message, "No authorization to download activity")
