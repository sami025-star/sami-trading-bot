import time, json, math, urllib.request, urllib.parse
from urllib.parse import quote

TOKEN = "8723033036:AAFB9Em6l1BpIsJhBt5VazeGAciE7VXnQV4"
CHAT_ID = "1442211942"

last_update_id = 0

WATCHLIST = ["SPX", "SPY", "QQQ", "INTC", "MU"]

SYMBOLS = {

    "SPX": "^GSPC",

    "SPY": "SPY",

    "QQQ": "QQQ",

    "AMD": "AMD",

    "NVDA": "NVDA",

    "TSLA": "TSLA",

    "INTC": "INTC",

    "MU": "MU"

}

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": msg
    }).encode()
    urllib.request.urlopen(url, data=data, timeout=15)

def ema(values, period):
    if len(values) < period:
        return values[-1]
    k = 2 / (period + 1)
    e = values[0]
    for p in values[1:]:
        e = p * k + e * (1 - k)
    return e

def rsi(values, period=14):
    if len(values) < period + 1:
        return 50
    gains = 0
    losses = 0
    recent = values[-period-1:]
    for i in range(1, len(recent)):
        diff = recent[i] - recent[i-1]
        if diff > 0:
            gains += diff
        else:
            losses += abs(diff)
    if losses == 0:
        return 100
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def atr(highs, lows, closes, period=14):
    if len(closes) < period + 1:
        return 0
    trs = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
        trs.append(tr)
    return sum(trs[-period:]) / period

def vwap(highs, lows, closes, vols):
    total_pv = 0
    total_v = 0
    for h, l, c, v in zip(highs, lows, closes, vols):
        typical = (h + l + c) / 3
        total_pv += typical * v
        total_v += v
    if total_v == 0:
        return closes[-1]
    return total_pv / total_v

def macd(values):
    if len(values) < 35:
        return 0
    macd_line = ema(values[-60:], 12) - ema(values[-60:], 26)
    signal = ema([macd_line] * 9, 9)
    return macd_line - signal

def get_chart(symbol, interval="5m", range_="1d"):
    ysymbol = quote(SYMBOLS[symbol])
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ysymbol}?interval={interval}&range={range_}"
    data = get_json(url)

    result = data["chart"]["result"][0]
    meta = result["meta"]
    q = result["indicators"]["quote"][0]

    closes = [x for x in q["close"] if x is not None]
    highs = [x for x in q["high"] if x is not None]
    lows = [x for x in q["low"] if x is not None]
    vols = [x for x in q["volume"] if x is not None]

    return meta, closes, highs, lows, vols

def trend_name(closes):
    if len(closes) < 25:
        return "غير واضح"
    e9 = ema(closes[-40:], 9)
    e21 = ema(closes[-40:], 21)
    price = closes[-1]

    if price > e9 > e21:
        return "صاعد"
    if price < e9 < e21:
        return "هابط"
    return "متذبذب"

def choose_strike(price, direction, symbol):
    if symbol == "SPX":
        step = 5
    elif symbol in ["SPY", "QQQ"]:
        step = 1
    else:
        step = 5

    if direction == "CALL":
        return f"{((int(price / step) + 1) * step)} CALL"
    if direction == "PUT":
        return f"{(int(price / step) * step)} PUT"
    return "-"

def stars(score):
    if score >= 85:
        return "⭐⭐⭐⭐⭐"
    if score >= 70:
        return "⭐⭐⭐⭐☆"
    if score >= 55:
        return "⭐⭐⭐☆☆"
    if score >= 40:
        return "⭐⭐☆☆☆"
    return "⭐☆☆☆☆"

def analyze(symbol):
    try:
        meta, closes, highs, lows, vols = get_chart(symbol, "5m", "1d")

        if len(closes) < 30:
            return f"⚠️ بيانات {symbol} غير كافية الآن"

        price = meta.get("regularMarketPrice", closes[-1])
        prev = meta.get("previousClose", closes[-2])
        market_state = meta.get("marketState", "UNKNOWN")

        change = round(price - prev, 2)
        percent = round((change / prev) * 100, 2) if prev else 0

        ema9 = ema(closes[-40:], 9)
        ema21 = ema(closes[-40:], 21)
        rsi_v = rsi(closes)
        atr_v = atr(highs, lows, closes)
        vwap_v = vwap(highs, lows, closes, vols)
        macd_v = macd(closes)

        support = round(min(lows[-21:-1]), 2)
        resistance = round(max(highs[-21:-1]), 2)

        current_vol = vols[-1] if vols else 0
        avg_vol = sum(vols[-20:]) / min(len(vols), 20) if vols else 0

        try:
            _, c1, _, _, _ = get_chart(symbol, "1m", "1d")
            trend_1m = trend_name(c1)
        except:
            trend_1m = "غير متوفر"

        trend_5m = trend_name(closes)

        try:
            _, c15, _, _, _ = get_chart(symbol, "15m", "5d")
            trend_15m = trend_name(c15)
        except:
            trend_15m = "غير متوفر"

        call_score = 0
        put_score = 0
        reasons = []

        if price > ema9 > ema21:
            call_score += 20
            reasons.append("EMA صاعد")
        if price < ema9 < ema21:
            put_score += 20
            reasons.append("EMA هابط")

        if price > vwap_v:
            call_score += 15
            reasons.append("السعر فوق VWAP")
        if price < vwap_v:
            put_score += 15
            reasons.append("السعر تحت VWAP")

        if macd_v > 0:
            call_score += 10
            reasons.append("MACD إيجابي")
        if macd_v < 0:
            put_score += 10
            reasons.append("MACD سلبي")

        if 52 <= rsi_v <= 72:
            call_score += 15
            reasons.append("RSI مناسب للصعود")
        if 28 <= rsi_v <= 48:
            put_score += 15
            reasons.append("RSI مناسب للهبوط")

        breakout = price > resistance
        breakdown = price < support

        if breakout:
            call_score += 20
            reasons.append("اختراق مقاومة")
        if breakdown:
            put_score += 20
            reasons.append("كسر دعم")

        if avg_vol > 0 and current_vol > avg_vol * 1.3 and change > 0:
            call_score += 10
            reasons.append("فوليوم شرائي")
        if avg_vol > 0 and current_vol > avg_vol * 1.3 and change < 0:
            put_score += 10
            reasons.append("فوليوم بيعي")

        if trend_1m == trend_5m == trend_15m == "صاعد":
            call_score += 10
            reasons.append("توافق الفريمات صعود")
        if trend_1m == trend_5m == trend_15m == "هابط":
            put_score += 10
            reasons.append("توافق الفريمات هبوط")

        fake_breakout = False
        if len(closes) >= 3:
            if closes[-2] > resistance and closes[-1] < resistance:
                fake_breakout = True
            if closes[-2] < support and closes[-1] > support:
                fake_breakout = True

        if fake_breakout:
            call_score -= 20
            put_score -= 20
            reasons.append("تحذير Fake Breakout")

        call_score = max(0, min(call_score, 100))
        put_score = max(0, min(put_score, 100))

        ai_score = max(call_score, put_score)

        if call_score >= 75 and call_score > put_score and rsi_v < 75 and not fake_breakout:
            decision = "🚀 CALL قوي"
            direction = "CALL"
            strike = choose_strike(price, "CALL", symbol)
            entry = f"ادخل فوق {resistance} بعد ثبات شمعة 5m"
            stop = round(price - atr_v, 2)
            tp1 = round(price + atr_v, 2)
            tp2 = round(price + atr_v * 2, 2)
        elif put_score >= 75 and put_score > call_score and rsi_v > 25 and not fake_breakout:
            decision = "🩸 PUT قوي"
            direction = "PUT"
            strike = choose_strike(price, "PUT", symbol)
            entry = f"ادخل تحت {support} بعد ثبات شمعة 5m"
            stop = round(price + atr_v, 2)
            tp1 = round(price - atr_v, 2)
            tp2 = round(price - atr_v * 2, 2)
        else:
            decision = "👀 انتظار"
            direction = "WAIT"
            strike = "لا يوجد Strike مناسب الآن"
            entry = "لا تدخل حتى يحصل اختراق/كسر مؤكد"
            stop = "-"
            tp1 = "-"
            tp2 = "-"

        market_msg = "🟢 السوق مفتوح" if market_state == "REGULAR" else "🔴 السوق مغلق أو البيانات ليست لحظية"
        volume_msg = "⚠️ الفوليوم غير واضح" if current_vol == 0 else "✅ الفوليوم متوفر"
        reason_text = "، ".join(reasons[-6:]) if reasons else "لا توجد أسباب قوية"

        return f"""
📊 تحليل {symbol}

{market_msg}

💰 السعر الحالي: {round(price, 2)}
📉 الإغلاق السابق: {round(prev, 2)}
📈 التغير: {change} ({percent}%)

📌 الدعم: {support}
📌 المقاومة: {resistance}

📈 EMA9: {round(ema9, 2)}
📉 EMA21: {round(ema21, 2)}
📍 VWAP: {round(vwap_v, 2)}
💪 RSI: {round(rsi_v, 1)}
📊 MACD: {round(macd_v, 3)}
⚡ ATR: {round(atr_v, 2)}

🕒 الفريمات:
1m: {trend_1m}
5m: {trend_5m}
15m: {trend_15m}

🔥 الفوليوم:
الحالي: {current_vol}
المتوسط: {int(avg_vol)}
{volume_msg}

🎯 القرار:
{decision}

🧠 AI Score:
{ai_score}% {stars(ai_score)}

📑 السترايك:
{strike}

⏰ الدخول:
{entry}

🎯 الأهداف:
TP1: {tp1}
TP2: {tp2}

🛑 الوقف:
{stop}

⚠️ التحذير:
{"Fake Breakout محتمل" if fake_breakout else "لا يوجد Fake Breakout واضح"}

📝 الأسباب:
{reason_text}

⚠️ لا تدخل إذا القرار انتظار أو AI Score أقل من 75%.
"""

    except Exception as e:
        return f"⚠️ خطأ في تحليل {symbol}:\n{e}"

def get_updates():
    global last_update_id

    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
    data = get_json(url)

    for item in data.get("result", []):
        last_update_id = item["update_id"]
        text = item.get("message", {}).get("text", "").upper().strip()

        if text in SYMBOLS:
            send(analyze(text))
        elif text == "تحليل":
            send(analyze("SPX"))
        elif text == "HELP":
            send("اكتب:\nSPX\nSPY\nQQQ\nAMD\nNVDA\nTSLA\nتحليل")
        elif text == "BEST":
            best = None
            best_score = -1
            best_msg = ""

            for s in SYMBOLS:
                msg = analyze(s)
                score = 0
                if "AI Score:" in msg:
                    try:
                        part = msg.split("AI Score:")[1].split("%")[0]
                        score = int(part.strip())
                    except:
                        score = 0

                if score > best_score:
                    best_score = score
                    best = s
                    best_msg = msg

            send(f"🔥 أفضل فرصة الآن: {best}\n\n{best_msg}")

send("✅ Sami Trading Bot Pro اشتغل بنجاح")

while True:
    try:
        get_updates()
        time.sleep(3)
    except Exception as e:
        print("Error:", e)
        time.sleep(5)
