from unittest import mock

import pytz

from tapiriik.testing.testtools import TapiriikTestCase, TestTools
from tapiriik.testing.services.Strava.connection_stubs import FileLoader
from tapiriik.services.Strava import StravaService
from tapiriik.services.interchange import Lap

TEST_ACTIVITY_ID = 692697310

class StravaServiceDownloadActivityTests(TapiriikTestCase):
    def setUp(self):
        svc = TestTools.create_mock_service('Strava')
        self.svcRecord = TestTools.create_mock_svc_record(svc)
        self.svcRecord.Authorization = {"OAuthToken": "token"}
        self.activity = TestTools.create_blank_activity(record=self.svcRecord)
        self.activity.ServiceData = {"Manual": False, "ActivityID": 1}

    def testManualActivitySetsSimpleLap(self):
        self.activity.ServiceData["Manual"] = True
        StravaService().DownloadActivity(self.svcRecord, self.activity)
        self.assertEqual(len(self.activity.Laps), 1)
        expected_lap = Lap(startTime=self.activity.StartTime,
                           endTime=self.activity.EndTime,
                           stats=self.activity.Stats)
        self.assertLapsEqual(self.activity.Laps[0], expected_lap)

    @mock.patch('tapiriik.services.Strava.connection')
    def testConnectionGetActivityIsCalled(self, mock_connection):
        self.activity.ServiceData["ActivityID"] = TEST_ACTIVITY_ID
        self.activity.StartTime = self.activity.StartTime.replace(tzinfo=pytz.utc)
        streamdata = FileLoader.getActivity(TEST_ACTIVITY_ID, None)
        mock_connection.getActivity.return_value = streamdata
        StravaService().DownloadActivity(self.svcRecord, self.activity,
                                         connection=mock_connection)
        mock_connection.getActivity.assert_called()

    @mock.patch('tapiriik.services.Strava.activity_gateway')
    def testActivityGatewayGetWaypointsCalled(self, mock_gateway):
        self.activity.ServiceData["ActivityID"] = TEST_ACTIVITY_ID
        StravaService().DownloadActivity(self.svcRecord, self.activity,
                                         connection=FileLoader)
        mock_gateway.get_waypoints.assert_called()

    def testActivityDataStoredInSingleLap(self):
        self.assertEqual(len(self.activity.Laps), 0)
        self.activity.ServiceData["ActivityID"] = TEST_ACTIVITY_ID
        StravaService().DownloadActivity(self.svcRecord, self.activity,
                                         connection=FileLoader)
        self.assertEqual(len(self.activity.Laps), 1)
        self.assertEqual(self.activity.Laps[0].Stats, self.activity.Stats)
        self.assertEqual(self.activity.Laps[0].StartTime, self.activity.StartTime)
        self.assertEqual(self.activity.Laps[0].EndTime, self.activity.EndTime)
