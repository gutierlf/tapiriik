import itertools
from datetime import timedelta

from tapiriik.services import APIException, UserException, UserExceptionType
from tapiriik.services.interchange import WaypointType, Waypoint, Location
from tapiriik.utilities import pairwise, get_list_of_dicts_from_dict_of_lists

def get_waypoints(activity, response):
    streamdata = _parseActivityJson(response)
    return _convertStreamsToWaypointsList(streamdata, activity.StartTime)

def _parseActivityJson(response):
    if response.status_code == 401:
        raise APIException("No authorization to download activity", block=True,
                           user_exception=UserException(UserExceptionType.Authorization,
                                                        intervention_required=True))
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
    ridedata = {stream["type"]: stream["data"] for stream in streamdata}
    waypoint_fields = _map_waypoint_fields(ridedata, startTime)
    waypoints = [Waypoint(**fields)
                 for fields in (_reshape_data_structure(waypoint_fields))]
    return waypoints[0:-1]

def _map_waypoint_fields(ridedata, startTime):
    return {
        'timestamp': _get_timestamps(ridedata['time'], startTime),
        'ptType'   : _get_types(ridedata['moving']),
        'location' : _get_locations(ridedata.get('latlng', []),
                                    ridedata.get('altitude', [])),
        'hr'       : ridedata.get('heartrate'      , []),
        'cadence'  : ridedata.get('cadence'        , []),
        'temp'     : ridedata.get('temp'           , []),
        'power'    : ridedata.get('watts'          , []),
        'speed'    : ridedata.get('velocity_smooth', []),
        'distance' : ridedata.get('distance'       , [])
    }

def _get_timestamps(times, startTime):
    return [startTime + timedelta(0, t) for t in times]

def _get_locations(latlngs, altitudes):
    def make_location(_latlng, _altitude):
        if _latlng is None or all(ll == 0 for ll in _latlng):
            lat = None
            lng = None
        else:
            lat = _latlng[0]
            lng = _latlng[1]
        alt = float(_altitude) if _altitude else None
        return Location(lat, lng, alt)

    return [make_location(latlng, altitude)
            for (latlng, altitude) in itertools.zip_longest(latlngs, altitudes)]

def _get_types(moving):
    def get_type_for_second_element():
        normal_pause_rule = [
            [True,  True,  False],
            [False, True , False]
        ]
        special_cases = [
            [False, False, False], # Paused prior to recording. Since first element always Start, put the Pause in second element
            [True , False, False] # Begin pause with recording, but first element always Start, so put the Pause in the second element
        ]
        rules = normal_pause_rule + special_cases

        is_pause = any(moving[0:3] == rule for rule in rules)
        return WaypointType.Pause if is_pause else WaypointType.Regular

    pause  = [current == True and nxt == False
              for (current, nxt) in pairwise(moving)] + [False]
    resume = [current == False and nxt == True
              for (current, nxt) in pairwise(moving)] + [False]

    movingCt = len(moving)
    return  [WaypointType.Start            if idx == 0 else
             get_type_for_second_element() if idx == 1 else
             WaypointType.End              if idx == movingCt - 2 else
             WaypointType.Pause            if pause[idx] else
             WaypointType.Resume           if resume[idx] else
             WaypointType.Regular
             for idx in range(0, movingCt - 1)]

def _reshape_data_structure(waypoint_fields):
    return get_list_of_dicts_from_dict_of_lists(waypoint_fields)
