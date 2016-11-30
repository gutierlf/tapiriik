import requests

from tapiriik.services import APIException, UserException, UserExceptionType

STRAVA_API_URL = "https://www.strava.com/api/v3/activities/"
STRAVA_ACTIVITY_DOWNLOAD_STREAMS = "/streams/time,altitude,heartrate,cadence,watts,temp,moving,latlng,distance,velocity_smooth"

def getActivity(activityID, headers):
    activityURL = STRAVA_API_URL + str(activityID) + STRAVA_ACTIVITY_DOWNLOAD_STREAMS
    return requests.get(activityURL, headers=headers)

def parseValidJson(response):
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