import requests
from datetime import datetime

def get_live_agricultural_risk(lat, lon):
    """
    Calls Open-Meteo API (Free, No API Key) to get live weather and soil moisture.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,precipitation,soil_moisture_0_to_7cm_mean",
        "daily": "precipitation_sum,temperature_2m_max",
        "timezone": "Asia/Phnom_Penh",
        "forecast_days": 7
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        current = data.get('current', {})
        daily = data.get('daily', {})
        
        current_temp = current.get('temperature_2m')
        current_rain = current.get('precipitation', 0)
        soil_moisture = current.get('soil_moisture_0_to_7cm_mean')
        rain_forecast = sum(daily.get('precipitation_sum', [0]*7))
        
        risk_level = "Normal Conditions"
        risk_color = "green"
        
        if current_rain > 30 or rain_forecast > 100:
            risk_level = "⚠️ High Flood Risk (Live)"
            risk_color = "red"
        elif soil_moisture is not None and soil_moisture < 0.15:
            risk_level = "⚠️ High Drought Risk (Live)"
            risk_color = "orange"
            
        return {
            "success": True,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "current_temp": current_temp,
            "current_rain": current_rain,
            "soil_moisture": soil_moisture,
            "7_day_rain_forecast": rain_forecast,
            "live_risk_assessment": risk_level,
            "risk_color": risk_color
        }
    except Exception as e:
        return {"success": False, "error": str(e)}