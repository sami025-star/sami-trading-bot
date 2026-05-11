import time, json, urllib.request
from urllib.parse import quote

TOKEN = "8723033036:AAFB9Em6l1BpIsJhBt5VazeGAciE7VXnQV4"
CHAT_ID = "1442211942"
last_update_id = 0

SYMBOLS = {
    "SPX": "^GSPC",
    "SPY": "SPY",
    "QQQ": "QQQ",
    "AMD": "AMD",
    "NVDA": "NVDA",
    "TSLA": "TSLA"
}

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = f"chat_id={CHAT_ID}&text={quote(msg)}".encode()
    urllib.request.urlopen(url, data=data, timeout=15)

def get_price(symbol):
    ysymbol = quote(SYMBOLS[symbol])
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ysymbol}?interval=5m&range=1d"
    data = get_json(url)
    meta = data["chart"]["result"][0]["meta"]
    price = meta.get("regularMarketPrice", 0)
    prev = meta.get("previousClose", 0)
    change = round(price - prev, 2)
    percent = round((change / prev) * 100, 2) if prev else 0
    return price, change, percent

def analyze(symbol):
    try:
        price, change, percent = get_price(symbol)
        signal = "CALL 🚀" if change > 0 else "PUT 🩸"
        return f"""📊 تحليل {symbol}

💰 السعر: {price}
📈 التغير: {change} ({percent}%)

🎯 الإشارة:
{signal}

🤖 البوت يعمل بنجاح"""
    except Exception as e:
        return f"⚠️ خطأ:\n{e}"

def get_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
    data = get_json(url)

    for item in data.get("result", []):
        last_update_id = item["update_id"]
        text = item.get("message", {}).get("text", "").upper().strip()

        if text in SYMBOLS:
            send(analyze(text))
        elif text == "HELP":
            send("اكتب:\nSPX\nSPY\nQQQ\nAMD\nNVDA\nTSLA")

send("✅ Sami Trading Bot اشتغل بنجاح")

while True:
    get_updates()
    time.sleep(3)