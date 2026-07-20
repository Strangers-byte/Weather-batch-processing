from weather_api import WeatherAPIClient

weather = WeatherAPIClient()

GERMAN_CITIES = [
    {
        "city_id": "berlin",
        "city_name": "Berlin",
        "country": "DE",
        "lat": 52.5200,
        "lon": 13.4050
    },
    {
        "city_id": "hamburg",
        "city_name": "Hamburg",
        "country": "DE",
        "lat": 53.5511,
        "lon": 9.9937
    },
    {
        "city_id": "munich",
        "city_name": "Munich",
        "country": "DE",
        "lat": 48.1351,
        "lon": 11.5820
    },
    {
        "city_id": "cologne",
        "city_name": "Cologne",
        "country": "DE",
        "lat": 50.9375,
        "lon": 6.9603
    },
    {
        "city_id": "frankfurt",
        "city_name": "Frankfurt",
        "country": "DE",
        "lat": 50.1109,
        "lon": 8.6821
    },
    {
        "city_id": "stuttgart",
        "city_name": "Stuttgart",
        "country": "DE",
        "lat": 48.7758,
        "lon": 9.1829
    },
    {
        "city_id": "duesseldorf",
        "city_name": "Düsseldorf",
        "country": "DE",
        "lat": 51.2277,
        "lon": 6.7735
    },
    {
        "city_id": "leipzig",
        "city_name": "Leipzig",
        "country": "DE",
        "lat": 51.3397,
        "lon": 12.3731
    },
    {
        "city_id": "dortmund",
        "city_name": "Dortmund",
        "country": "DE",
        "lat": 51.5136,
        "lon": 7.4653
    },
    {
        "city_id": "essen",
        "city_name": "Essen",
        "country": "DE",
        "lat": 51.4556,
        "lon": 7.0116
    }
]

weather.city_data_for_API(GERMAN_CITIES)