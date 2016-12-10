import requests

STRAVA_API_URL = "https://www.strava.com/api/v3/activities/"
STRAVA_ACTIVITY_DOWNLOAD_STREAMS = "/streams/time,altitude,heartrate,cadence,watts,temp,moving,latlng,distance,velocity_smooth"

def getActivity(activityID, headers):
    activityURL = STRAVA_API_URL + str(activityID) + STRAVA_ACTIVITY_DOWNLOAD_STREAMS
    response = requests.get(activityURL, headers=headers)
    return response

def apiHeader(oAuthToken):
    return {"Authorization": "access_token " + oAuthToken}

def getActivityWithOAuthToken(activity, oAuthToken, connection):
    headers = apiHeader(oAuthToken)
    response = connection.getActivity(activity.ServiceData["ActivityID"], headers)
    return response