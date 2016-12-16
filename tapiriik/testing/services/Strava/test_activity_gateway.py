import datetime

from tapiriik.testing.testtools import TapiriikTestCase
from tapiriik.testing.services.Strava.connection_stubs import HTTP_FOUR_OH_ONE_RESPONSE, HTTP_NO_JSON_RESPONSE, \
    HTTP_RECORD_NOT_FOUND_RESPONSE, HTTP_ERROR_IN_DOWNLOADED_DATA_RESPONSE
from tapiriik.services.Strava.activity_gateway import _parseActivityJson, _convertStreamsToWaypointsList
from tapiriik.services.api import APIException
from tapiriik.services.interchange import WaypointType

class StravaActivityGatewayParseResponseTests(TapiriikTestCase):
    def testStatusCode401RaisesAPIException(self):
        self.assertDownloadActivityRaisesAPIException(
            HTTP_FOUR_OH_ONE_RESPONSE, "No authorization to download activity")

    def testMissingJsonRaisesAPIException(self):
        self.assertDownloadActivityRaisesAPIException(
            HTTP_NO_JSON_RESPONSE, "Stream data returned is not JSON")

    def testRecordNotFoundMessageRaisesAPIException(self):
        self.assertDownloadActivityRaisesAPIException(
            HTTP_RECORD_NOT_FOUND_RESPONSE, "Could not find activity")

    def testErrorInDownloadedDataRaisesAPIException(self):
        self.assertDownloadActivityRaisesAPIException(
            HTTP_ERROR_IN_DOWNLOADED_DATA_RESPONSE, "Strava error the error message")

    def assertDownloadActivityRaisesAPIException(self, response, message):
        with self.assertRaises(APIException) as cm:
            _parseActivityJson(response)
        self.assertEqual(cm.exception.Message, message)

class StravaActivityGatewayConvertStreamsTests(TapiriikTestCase):
    startTime = datetime.datetime(2016, 12, 13, 0, 35, 44, 113225)
    time_and_moving_streams = {'time': [0, 1, 2, 3], 'moving': [True, True, True, True]}

    def convert(self, stream_dict):
        stream_list = [{'type': k, 'data': v} for (k, v) in stream_dict.items()]
        return _convertStreamsToWaypointsList(stream_list, self.startTime)

    def testTimeIsRequiredStream(self):
        streams = {}
        self.assertRaisesRegex(KeyError, 'time', self.convert, streams)

    def testMovingIsRequiredStream(self):
        streams = {'time': [0]}
        self.assertRaisesRegex(KeyError, 'moving', self.convert, streams)

    def testRemainingFieldsAreOptional(self):
        streams = {'time': [0], 'moving': [True]}
        self.convert(streams)

    def testConversionRemovesLastDataElement(self):
        streams = self.time_and_moving_streams
        waypoints = self.convert(streams)
        self.assertEqual(len(waypoints), len(streams['time']) - 1)

    def testStravaHeartrateBecomesWaypointHR(self):
        self.assertCorrectFieldMapping('heartrate', 'HR')

    def testStravaCadenceBecomesWaypointCadence(self):
        self.assertCorrectFieldMapping('cadence', 'Cadence')

    def testStravaTempBecomesWaypointTemp(self):
        self.assertCorrectFieldMapping('temp', 'Temp')

    def testStravaWattsBecomesWaypointPower(self):
        self.assertCorrectFieldMapping('watts', 'Power')

    def testStravaVelocitySmoothBecomesWaypointSpeed(self):
        self.assertCorrectFieldMapping('velocity_smooth', 'Speed')

    def testStravaDistanceBecomesWaypointDistance(self):
        self.assertCorrectFieldMapping('distance', 'Distance')

    def assertCorrectFieldMapping(self, strava_field_name, waypoint_field_name):
        streams = {'time': [0, 1], 'moving': [True, True],
                   'heartrate': ['heartrate', 0],
                   'cadence': ['cadence', 0],
                   'temp': ['temp', 0],
                   'watts': ['watts', 0],
                   'velocity_smooth': ['velocity_smooth', 0],
                   'distance': ['distance', 0]
                   }
        waypoint = self.convert(streams)[0]
        self.assertEqual(getattr(waypoint, waypoint_field_name), strava_field_name)

    def testStravaTimesMappedToWaypointTimestamps(self):
        waypoint = self.convert(self.time_and_moving_streams)[0]
        self.assertEqual(waypoint.Timestamp, self.startTime)

    def testFirstWaypointTypeIsStart(self):
        waypoints = self.convert(self.time_and_moving_streams)
        self.assertEqual(waypoints[0].Type, WaypointType.Start)

    def testLastWaypointTypeIsEnd(self):
        waypoints = self.convert(self.time_and_moving_streams)
        self.assertEqual(waypoints[-1].Type, WaypointType.End)

    def testOtherWaypointsDefaultToTypeRegular(self):
        waypoints = self.convert(self.time_and_moving_streams)
        self.assertEqual(waypoints[1].Type, WaypointType.Regular)

    middle_pause = {'time': [0, 1, 2, 3, 4, 5], 'moving': [True, True, False, False, True, True]}

    def testStravaMovingDeterminesPauses(self):
        waypoints = self.convert(self.middle_pause)
        any_pauses = any(waypoint.Type == WaypointType.Pause for waypoint in waypoints)
        self.assertTrue(any_pauses)

    def testOnlyBeginningOfPausedSegmentGetsWaypointTypePause(self):
        waypoints = self.convert(self.middle_pause)
        self.assertEqual(waypoints[1].Type, WaypointType.Pause)

    def testMiddleOfPausedSegmentGetsWaypointTypeRegular(self):
        waypoints = self.convert(self.middle_pause)
        self.assertEqual(waypoints[2].Type, WaypointType.Regular)

    def testWaypointTypeResumeAfterPausedSegment(self):
        waypoints = self.convert(self.middle_pause)
        self.assertEqual(waypoints[3].Type, WaypointType.Resume)

    def testWhenPauseBeginsAtSecondElementThenSecondWaypointTypeIsPause(self):
        streams = {'time': [0, 1, 2], 'moving': [True, True, False]}
        self.assertSecondConvertedTypeIsPause(streams)
        streams['moving'] = [False, True, False]
        self.assertSecondConvertedTypeIsPause(streams)

    def testWhenPauseBeginsBeforeRecordingThenSecondWaypointTypeIsPause(self):
        streams = {'time': [0, 1, 2], 'moving': [False, False, False]}
        self.assertSecondConvertedTypeIsPause(streams)

    def testWhenPauseBeginsWithRecordingThenSecondWaypointTypeIsPause(self):
        streams = {'time': [0, 1, 2], 'moving': [True, False, False]}
        self.assertSecondConvertedTypeIsPause(streams)

    def assertSecondConvertedTypeIsPause(self, streams):
        waypoints = self.convert(streams)
        self.assertEqual(waypoints[1].Type, WaypointType.Pause)

    latlng_and_altitude = {'time': [0, 1, 2], 'moving': [True, True, True],
                           'latlng': [[1.0, 2.0], [0, 0], [1.1, 2.1]],
                           'altitude': [1, 2, 3]}
    def testStravaLatlngAndAltitudeMappedToWaypointLocation(self):
        waypoints = self.convert(self.latlng_and_altitude)
        location = waypoints[0].Location
        self.assertEqual(location.Latitude, self.latlng_and_altitude['latlng'][0][0])
        self.assertEqual(location.Longitude, self.latlng_and_altitude['latlng'][0][1])
        self.assertEqual(location.Altitude, self.latlng_and_altitude['altitude'][0])

    def testLatlngIsOptional(self):
        altitude = self.latlng_and_altitude.copy()
        altitude.pop('latlng')
        waypoints = self.convert(altitude)
        location = waypoints[0].Location
        self.assertIsNone(location.Latitude)
        self.assertIsNone(location.Longitude)
        self.assertEqual(location.Altitude, altitude['altitude'][0])

    def testAltitudeIsOptional(self):
        latlng = self.latlng_and_altitude.copy()
        latlng.pop('altitude')
        waypoints = self.convert(latlng)
        location = waypoints[0].Location
        self.assertEqual(location.Latitude, latlng['latlng'][0][0])
        self.assertEqual(location.Longitude, latlng['latlng'][0][1])
        self.assertIsNone(location.Altitude)

    def testWhenLatlngBothZeroThenWaypointLatlngBothNone(self):
        waypoints = self.convert(self.latlng_and_altitude)
        location = waypoints[1].Location
        self.assertIsNone(location.Latitude);
        self.assertIsNone(location.Longitude)
