import os
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


class SatelliteAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("QWEN_API_KEY")
        self.base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"

        if not self.api_key:
            raise ValueError("QWEN_API_KEY not found in environment variables")

    def analyze_image(self, image_path):
        """Analyze agricultural satellite image using Qwen-VL"""
        try:
            with open(image_path, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "qwen-vl-max",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                            },
                            {
                                "type": "text",
                                "text": "Analyze this agricultural satellite image. Return ONLY a JSON object with: crop_health (Good/Moderate/Poor), water_present (true/false), risk_level (Low/Medium/High), analysis (one sentence summary)"
                            }
                        ]
                    }
                ],
                "max_tokens": 500
            }

            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            result = response.json()
            text = result["choices"][0]["message"]["content"]

            if isinstance(text, list):
                text = "".join(part.get("text", "") for part in text if isinstance(part, dict))

            import json
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            json_data = json.loads(text[json_start:json_end])

            return json_data

        except Exception as e:
            return {"error": str(e), "risk_level": "Unknown"}