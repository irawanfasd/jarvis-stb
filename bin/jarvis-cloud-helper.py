#!/usr/bin/env python3
"""Groq cloud helper — dipanggil oleh jarvis via subprocess."""
import os, sys, json, urllib.request, time

key = os.environ.get('GROQ_API_KEY', '').strip()
model = os.environ.get('JARVIS_GROQ_MODEL', 'openai/gpt-oss-120b')

CHROME_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
             "AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/124.0.0.0 Safari/537.36")

def main():
    if not key:
        print(json.dumps({"error": "GROQ_API_KEY tidak di-set"}))
        sys.exit(0)

    try:
        payload = json.loads(sys.stdin.read())
    except Exception as e:
        print(json.dumps({"error": f"input bukan JSON: {e}"}))
        sys.exit(0)

    messages = payload.get("messages", [])
    num_predict = payload.get("num_predict", 500)
    timeout = payload.get("timeout", 20)

    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": num_predict,
    }

    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": CHROME_UA,
                "Accept": "application/json",
            },
            method="POST",
        )
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        elapsed = time.time() - t0
        msg = data["choices"][0]["message"]
        content = (msg.get("content") or msg.get("reasoning") or "").strip()
        if not content:
            print(json.dumps({"error": "konten kosong dari Groq"}))
        else:
            print(json.dumps({"content": content, "elapsed": elapsed}))
    except urllib.error.HTTPError as e:
        err = ""
        try: err = e.read().decode()[:300]
        except: pass
        print(json.dumps({"error": f"HTTP {e.code}: {err or e.reason}"}))
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}))

if __name__ == "__main__":
    main()
