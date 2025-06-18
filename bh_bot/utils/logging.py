from datetime import datetime


def tprint(text):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")
