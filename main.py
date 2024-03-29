import datetime as dt
import json
import requests

from flask import Flask, jsonify, request

API_TOKEN = ""

VISUAL_CROSSING_WEATHER_API_KEY = ""

VISUAL_CROSSING_WEATHER_API_BASE_URL = ("https://weather.visualcrossing.com/"
                                        "VisualCrossingWebServices/rest/services/timeline/")

OPENAI_API_KEY = ""

OPENAI_API_BASE_URL = "https://api.openai.com/v1/chat/completions"

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def get_weather_forecast(location: str, payload: str, include: str):
    url = (f"{VISUAL_CROSSING_WEATHER_API_BASE_URL}/{location}/{payload}?unitGroup=metric"
           f"&key={VISUAL_CROSSING_WEATHER_API_KEY}&include={include}")

    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        return json.loads(response.text)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


def map_hourly_weather_forecast(response: json):
    result = []

    for hour_forecast in response["days"][0]["hours"]:
        result.append({
            "time": hour_forecast["datetime"],
            "conditions": hour_forecast["conditions"],
            "temp_c": hour_forecast["temp"],
            "feels_like_c": hour_forecast["feelslike"],
            "wind_kph": hour_forecast["windspeed"],
            "humidity": hour_forecast["humidity"],
            "precipitation_mm": hour_forecast["precip"],
            "pressure_mb": hour_forecast["pressure"],
            "uv_index": hour_forecast["uvindex"],
        })

    return result


def get_hourly_weather_forecast(location: str, date: str):
    response = get_weather_forecast(location, date, "hours")

    return map_hourly_weather_forecast(response)


def map_daily_weather_forecast(response: json):
    result = []

    for day_forecast in response["days"]:
        result.append({
            "date": day_forecast["datetime"],
            "conditions": day_forecast["conditions"],
            "description": day_forecast["description"],
            "temp_c": day_forecast["temp"],
            "feels_like_c": day_forecast["feelslike"],
            "wind_kph": day_forecast["windspeed"],
            "humidity": day_forecast["humidity"],
            "precipitation_mm": day_forecast["precip"],
            "pressure_mb": day_forecast["pressure"],
            "uv_index": day_forecast["uvindex"]
        })

    return result


def get_daily_weather_forecast(location: str, date: str):
    response = get_weather_forecast(location, date, "days")

    return map_daily_weather_forecast(response)[0]


def get_next_10_days_weather(location: str):
    response = get_weather_forecast(location, "next10days", "days")

    return map_daily_weather_forecast(response)


def get_clothes_suggestion(weather: json):
    response = requests.post(
        url=OPENAI_API_BASE_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{
                "role": "user",
                "content": f"Suggest clothes suitable for this weather, listed as comma-separated items without any "
                           f"additional information or explanations: {json.dumps(weather)}"
            }]
        }
    )

    if response.status_code == requests.codes.ok:
        return json.loads(response.text)["choices"][0]["message"]["content"]
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/api/v1/hourly", methods=["POST"])
def hourly_weather_endpoint():
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)
    elif json_data.get("location") is None:
        raise InvalidUsage("location is required", status_code=400)
    elif json_data.get("date") is None:
        raise InvalidUsage("date is required", status_code=400)
    elif json_data.get("requester_name") is None:
        raise InvalidUsage("requester_name is required", status_code=400)

    token = json_data.get("token")
    location = json_data.get("location")
    date = json_data.get("date")
    requester_name = json_data.get("requester_name")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    hourly_weather = get_hourly_weather_forecast(location, date)

    result = {
        "timestamp": dt.datetime.now().isoformat(),
        "location": location,
        "date": date,
        "requester_name": requester_name,
        "weather": hourly_weather
    }

    return result


@app.route("/api/v1/daily", methods=["POST"])
def daily_weather_endpoint():
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)
    elif json_data.get("location") is None:
        raise InvalidUsage("location is required", status_code=400)
    elif json_data.get("date") is None:
        raise InvalidUsage("date is required", status_code=400)
    elif json_data.get("requester_name") is None:
        raise InvalidUsage("requester_name is required", status_code=400)

    token = json_data.get("token")
    location = json_data.get("location")
    date = json_data.get("date")
    requester_name = json_data.get("requester_name")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    daily_weather = get_daily_weather_forecast(location, date)
    suggested_clothes = get_clothes_suggestion(daily_weather)

    result = {
        "timestamp": dt.datetime.now().isoformat(),
        "location": location,
        "date": date,
        "requester_name": requester_name,
        "weather": daily_weather,
        "suggested_clothes": suggested_clothes
    }

    return result


@app.route("/api/v1/10-days", methods=["POST"])
def next_10_days_weather_endpoint():
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)
    elif json_data.get("location") is None:
        raise InvalidUsage("location is required", status_code=400)
    elif json_data.get("requester_name") is None:
        raise InvalidUsage("requester_name is required", status_code=400)

    token = json_data.get("token")
    location = json_data.get("location")
    requester_name = json_data.get("requester_name")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    daily_weather = get_next_10_days_weather(location)

    result = {
        "timestamp": dt.datetime.now().isoformat(),
        "location": location,
        "requester_name": requester_name,
        "weather": daily_weather
    }

    return result
