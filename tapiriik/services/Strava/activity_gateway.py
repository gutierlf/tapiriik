import itertools
from datetime import timedelta

from tapiriik.services import APIException, UserException, UserExceptionType
from tapiriik.services.interchange import WaypointType, Waypoint, Location

class ActivityGateway:

    def __init__(self, activity, response):
        streamdata = _parseActivityJson(response)
        self._waypoints = _convertStreamsToWaypointsList(streamdata, activity.StartTime)

    @property
    def waypoints(self):
        return self._waypoints

def _parseActivityJson(response):
    if response.status_code == 401:
        raise APIException("No authorization to download activity", block=True,
                           user_exception=UserException(UserExceptionType.Authorization, intervention_required=True))
    try:
        streamdata = response.json()
    except:
        raise APIException("Stream data returned is not JSON")
    if "message" in streamdata and streamdata["message"] == "Record Not Found":
        raise APIException("Could not find activity")
    errorMessage = [stream["data"] for stream in streamdata if stream["type"] == "error"]
    if errorMessage:
        raise APIException("Strava error " + errorMessage[0])
    return streamdata

def _convertStreamsToWaypointsList(streamdata, startTime):
    def make_location(latlng, altitude):
        if latlng is None or all(ll == 0 for ll in latlng):
            lat = None
            lng = None
        else:
            lat = latlng[0]
            lng = latlng[1]
        return Location(lat, lng, altitude)

    def pairwise(iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)

    def get_type_when_pause_at_beginning(moving_list):
        first_three_are_false = moving_list[0:3] == [False, False, False]
        return WaypointType.Pause if first_three_are_false else WaypointType.Regular

    ridedata = {stream["type"]: stream["data"] for stream in streamdata}

    times = [startTime + timedelta(0, t) for t in ridedata['time']]

    latlngs   = ridedata.get('latlng', [])
    altitudes = [float(altitude) for altitude in ridedata.get('altitude', [])]
    locations = [make_location(latlng, altitude)
                 for (latlng, altitude)
                 in itertools.zip_longest(latlngs, altitudes)]

    waypointCt = len(ridedata["time"])

    moving = ridedata['moving']
    pause  = [current == True and nxt == False
              for (current, nxt) in pairwise(moving)] + [False]
    resume = [current == False and nxt == True
              for (current, nxt) in pairwise(moving)] + [False]
    types = [WaypointType.Start                       if idx == 0 else
             get_type_when_pause_at_beginning(moving) if idx == 1 else
             WaypointType.End                         if idx == waypointCt - 2 else
             WaypointType.Pause                       if pause[idx] else
             WaypointType.Resume                      if resume[idx] else
             WaypointType.Regular
             for idx in range(0, waypointCt - 1)]

    hrs        = ridedata.get('heartrate'      , [])
    cadences   = ridedata.get('cadence'        , [])
    temps      = ridedata.get('temp'           , [])
    powers     = ridedata.get('watts'          , [])
    velocities = ridedata.get('velocity_smooth', [])
    distances  = ridedata.get('distance'       , [])

    waypoints = [Waypoint(timestamp=timestamp, location=location, ptType=the_type,
                          hr=hr, cadence=cadence, temp=temp, power=power,
                          speed=speed, distance=distance)
                 for (timestamp, location, the_type, hr, cadence, temp, power, speed, distance)
                 in itertools.zip_longest(times, locations, types, hrs, cadences, temps, powers, velocities, distances)]

    return waypoints[0:-1]
