import requests
from PIL import Image
import io
import json

# 建立簡單的測試圖片
img = Image.new("RGB", (200, 200), color="white")
from PIL import ImageDraw

draw = ImageDraw.Draw(img)
draw.ellipse([50, 50, 150, 150], fill="red", outline="darkred")

img_bytes = io.BytesIO()
img.save(img_bytes, format="PNG")
img_bytes.seek(0)

# 發送文件
try:
    files = {"image": ("test.png", img_bytes, "image/png")}
    r = requests.post("http://localhost:5000/api/recognize", files=files, timeout=60)
    print("Status:", r.status_code)

    if r.status_code == 200:
        data = r.json()
        print("Success:", data.get("success"))
        if data.get("success"):
            print("✓ Recognition successful!")
            items = data.get("recognized_items", [])
            print("Found", len(items), "results")
        else:
            print("Message:", data.get("message"))
    else:
        err = r.json()
        print("Error:", err.get("error", "Unknown error")[:300])
except Exception as e:
    print("Exception:", str(e)[:200])
