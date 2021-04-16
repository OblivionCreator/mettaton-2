import requests
import json


def getDiffCheck(left: str, right: str, expiry='forever', title='Differences'):
    r = requests.post("https://api.diffchecker.com/diffs", json={
        "left": left,
        "right": right,
        "expiry": expiry,
        "title": title})

    r_js = json.loads(r.text)
    d_url = r_js["slug"]
    return f"https://www.diffchecker.com/{d_url}"
