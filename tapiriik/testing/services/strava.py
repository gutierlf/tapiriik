from tapiriik.testing.testtools import TapiriikTestCase, TestTools
from tapiriik.testing.services.http_stubs import Http401Getter, HttpNoJsonGetter, HttpRecordNotFoundGetter, \
    HttpErrorInDownloadedDataGetter, FileLoader

from tapiriik.services.Strava import StravaService
from tapiriik.services.api import APIException
from tapiriik.services.interchange import Waypoint, WaypointType, Location

from datetime import timedelta
import pytz

TEST_ACTIVITY_ID = 692697310

class StravaServiceDownloadActivityTests(TapiriikTestCase):
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

    def testErrorInDownloadedDataRaisesAPIException(self):
        self.assertDownloadActivityRaisesAPIException(
            HttpErrorInDownloadedDataGetter, "Strava error the error message")

    def assertDownloadActivityRaisesAPIException(self, http_getter, message):
        with self.assertRaises(APIException) as cm:
            StravaService().DownloadActivity(self.svcRecord,
                                             self.activity,
                                             http_getter=http_getter)
        self.assertEqual(cm.exception.Message, message)

    def testActivityDataStoredInSingleLap(self):
        self.assertEqual(len(self.activity.Laps), 0)
        self.activity.ServiceData["ActivityID"] = TEST_ACTIVITY_ID
        StravaService().DownloadActivity(self.svcRecord, self.activity, http_getter=FileLoader)
        self.assertEqual(len(self.activity.Laps), 1)
        self.assertEqual(self.activity.Laps[0].Stats, self.activity.Stats)
        self.assertEqual(self.activity.Laps[0].StartTime, self.activity.StartTime)
        self.assertEqual(self.activity.Laps[0].EndTime, self.activity.EndTime)

    def testStreamProcessingFacts(self):
        self.activity.ServiceData["ActivityID"] = TEST_ACTIVITY_ID
        self.activity.StartTime = self.activity.StartTime.replace(tzinfo=pytz.utc)
        streamdata = FileLoader.getActivity(TEST_ACTIVITY_ID, None).json()
        expected_waypoints = self.convertStreamsToWaypointsList(streamdata, self.activity.StartTime)
        StravaService().DownloadActivity(self.svcRecord, self.activity, http_getter=FileLoader)
        actual_waypoints = self.activity.Laps[0].Waypoints
        self.assertWaypointsListsEqual(actual_waypoints, expected_waypoints)

    def convertStreamsToWaypointsList(self, streamdata, startTime):
        ridedata = {}
        for stream in streamdata:
            ridedata[stream["type"]] = stream["data"]

        waypoints = []

        hasHR = "heartrate" in ridedata and len(ridedata["heartrate"]) > 0
        hasCadence = "cadence" in ridedata and len(ridedata["cadence"]) > 0
        hasTemp = "temp" in ridedata and len(ridedata["temp"]) > 0
        hasPower = ("watts" in ridedata and len(ridedata["watts"]) > 0)
        hasAltitude = "altitude" in ridedata and len(ridedata["altitude"]) > 0
        hasDistance = "distance" in ridedata and len(ridedata["distance"]) > 0
        hasVelocity = "velocity_smooth" in ridedata and len(ridedata["velocity_smooth"]) > 0

        inPause = False

        waypointCt = len(ridedata["time"])
        for idx in range(0, waypointCt - 1):

            waypoint = Waypoint(startTime + timedelta(0, ridedata["time"][idx]))
            if "latlng" in ridedata:
                latlng = ridedata["latlng"][idx]
                waypoint.Location = Location(latlng[0], latlng[1], None)
                if waypoint.Location.Longitude == 0 and waypoint.Location.Latitude == 0:
                    waypoint.Location.Longitude = None
                    waypoint.Location.Latitude = None

            if hasAltitude:
                if not waypoint.Location:
                    waypoint.Location = Location(None, None, None)
                waypoint.Location.Altitude = float(ridedata["altitude"][idx])

            # When pausing, Strava sends this format:
            # idx = 100 ; time = 1000; moving = true
            # idx = 101 ; time = 1001; moving = true  => convert to Pause
            # idx = 102 ; time = 2001; moving = false => convert to Resume: (2001-1001) seconds pause
            # idx = 103 ; time = 2002; moving = true

            if idx == 0:
                waypoint.Type = WaypointType.Start
            elif idx == waypointCt - 2:
                waypoint.Type = WaypointType.End
            elif idx < waypointCt - 2 and ridedata["moving"][idx+1] and inPause:
                waypoint.Type = WaypointType.Resume
                inPause = False
            elif idx < waypointCt - 2 and not ridedata["moving"][idx+1] and not inPause:
                waypoint.Type = WaypointType.Pause
                inPause = True

            if hasHR:
                waypoint.HR = ridedata["heartrate"][idx]
            if hasCadence:
                waypoint.Cadence = ridedata["cadence"][idx]
            if hasTemp:
                waypoint.Temp = ridedata["temp"][idx]
            if hasPower:
                waypoint.Power = ridedata["watts"][idx]
            if hasVelocity:
                waypoint.Speed = ridedata["velocity_smooth"][idx]
            if hasDistance:
                waypoint.Distance = ridedata["distance"][idx]
            waypoints.append(waypoint)

        return waypoints