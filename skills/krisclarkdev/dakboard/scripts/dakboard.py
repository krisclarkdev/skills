#!/usr/bin/env python3
# SECURITY MANIFEST:
# Environment variables accessed: DAKBOARD_API_KEY (only)
# External endpoints called: https://dakboard.com/api/ (only)
# Local files read: none
# Local files written: none

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import argparse

def get_api_key():
    key = os.environ.get("DAKBOARD_API_KEY")
    if not key:
        print("Error: DAKBOARD_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return key

def make_request(method, endpoint, data=None):
    if endpoint.startswith("/v2/"):
        base = "https://dakboard.com/api"
    else:
        base = "https://dakboard.com/api/2"

    url = f"{base}/{endpoint.lstrip('/')}"
    api_key = get_api_key()
    body = None
    headers = {"Accept": "application/json"}

    is_form_encoded = (method == "PUT" and endpoint.startswith("/devices")) or \
                      (method == "POST" and endpoint.startswith("/v2/custom-message"))

    # Always add api_key to the URL
    if "?" in url:
        url += f"&api_key={api_key}"
    else:
        url += f"?api_key={api_key}"

    if is_form_encoded:
        body = urllib.parse.urlencode(data or {}).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            if not res_body.strip().startswith(("{", "[")):
                 return {"status": "success", "message": res_body}
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        print(f"Response: {error_body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error making request: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_get_devices(args):
    print(json.dumps(make_request("GET", "/devices"), indent=2))

def cmd_get_screens(args):
    print(json.dumps(make_request("GET", "/screens"), indent=2))

def cmd_update_device(args):
    print(json.dumps(make_request("PUT", f"/devices/{args.device_id}", data={"screen_id": args.screen_id}), indent=2))

def cmd_send_message(args):
    data = {"message": args.message}
    if args.serial_num:
        data['serial_numbers[]'] = args.serial_num
    print(json.dumps(make_request("POST", "/v2/custom-message", data=data), indent=2))

def cmd_push_metric(args):
    print(json.dumps(make_request("POST", "/metrics", data={args.key: args.value}), indent=2))

def cmd_push_fetch(args):
    print(json.dumps(make_request("POST", "/fetch", data=json.loads(args.json_data)), indent=2))

def main():
    parser = argparse.ArgumentParser(description="DAKboard API CLI Skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("devices", help="List all DAKboard devices.")
    subparsers.add_parser("screens", help="List all available screen layouts.")
    p_update = subparsers.add_parser("update-device", help="Update the screen layout on a device.")
    p_update.add_argument("device_id", help="The ID of the device (e.g., dev_xxxxxxxx).")
    p_update.add_argument("screen_id", help="The ID of the screen to assign (e.g., scr_xxxxxxxx).")
    p_msg = subparsers.add_parser("message", help="Send a message to a Custom Message block.")
    p_msg.add_argument("message", help="The text message to send.")
    p_msg.add_argument("--serial-num", help="Optional: The serial number of the target device.")
    p_metric = subparsers.add_parser("metric", help="Push a single data point to a Metrics block.")
    p_metric.add_argument("key", help="The name of the metric.")
    p_metric.add_argument("value", help="The value of the metric.")
    p_fetch = subparsers.add_parser("fetch", help="Push a JSON object to a Fetch block.")
    p_fetch.add_argument("json_data", help="The JSON object as a string.")

    args = parser.parse_args()
    
    cmd_map = {
        "devices": cmd_get_devices, "screens": cmd_get_screens, "update-device": cmd_update_device,
        "message": cmd_send_message, "metric": cmd_push_metric, "fetch": cmd_push_fetch,
    }
    cmd_map[args.command](args)

if __name__ == "__main__":
    main()
