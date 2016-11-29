from tapiriik.testing.testtools import TapiriikTestCase, TestTools
from tapiriik.testing.services.http_stubs import Http401Getter, HttpNoJsonGetter, HttpRecordNotFoundGetter

from tapiriik.services.Strava import StravaService
from tapiriik.services.api import APIException

class StravaServiceTests(TapiriikTestCase):
    def setUp(self):
        svc = TestTools.create_mock_service("Strava")
        self.svcRecord = TestTools.create_mock_svc_record(svc)
        self.svcRecord.Authorization = {"OAuthToken": "token"}
        self.activity = TestTools.create_blank_activity(record=self.svcRecord)
        self.activity.ServiceData = {"Manual": False, "ActivityID": 1}

    def testStatusCode401RaisesAPIException(self):
        self.assertDownloadActivityRaisesAPIException(
            Http401Getter, "No authorization to download activity")

    def testMissingJsonRaisesAPIException(self):
        self.assertDownloadActivityRaisesAPIException(
            HttpNoJsonGetter, "Stream data returned is not JSON")

    def testRecordNotFoundMessageRaisesAPIException(self):
        self.assertDownloadActivityRaisesAPIException(
            HttpRecordNotFoundGetter, "Could not find activity")

    def assertDownloadActivityRaisesAPIException(self, http_getter, message):
        with self.assertRaises(APIException) as cm:
            StravaService().DownloadActivity(self.svcRecord,
                                             self.activity,
                                             http_getter=http_getter)
        self.assertEqual(cm.exception.Message, message)

