import requests
import json

response = requests.get("http://127.0.0.1:8000/openapi.json")
spec = response.json()

# Find security schemes
if "components" in spec and "securitySchemes" in spec["components"]:
    print("Security Schemes:")
    print(json.dumps(spec["components"]["securitySchemes"], indent=2))
