"""
Get and output all slack conversations including threads in the channel specified by a channel_id.
"""
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from urllib import error, parse, request

ENDPOINT_URL = "https://slack.com/api"
USER_LIST_API_PATH = "users.list"
CONVERSATION_API_PATH = "conversations.history"
REPLY_API_PATH = "conversations.replies"


def convert_to_jst_dt(ts: float) -> dt.datetime:
    """
    Convert UNIX timestamp to JST datetime YYYY-MM-DD HH:mm:ss.ffffff+09:00.
    """
    return dt.datetime.fromtimestamp(ts, dt.timezone(dt.timedelta(hours=9)))


def setup_request(api_path: str, channel_id: str, params: dict = None) -> request.Request:
    """
    Setup valid request with token and channel_id.
    """

    TOKEN = os.getenv("SLACK_API_TOKEN")
    if TOKEN is None:
        print("You need to set environment variable 'SLACK_API_TOKEN' first.")
        sys.exit(1)
    AUTH_HEADER = {
        "Authorization": f"Bearer {TOKEN}",
    }
    request_url = f"{ENDPOINT_URL}/{api_path}?channel={channel_id}"
    if params is not None:
        request_url = f"{request_url}&{parse.urlencode(params)}"
    return request.Request(request_url, None, AUTH_HEADER)


def get_user_info() -> dict:
    """
    Get all user info in the workspace.
    """
    user_map = {}
    cursor = ""
    try:
        while True:
            req = setup_request(USER_LIST_API_PATH, args.channel_id, {"cursor": cursor})
            with request.urlopen(req) as res:
                body = json.loads(res.read())
            if not body["ok"]:
                print(f'request FAILED: {body["error"]}')
                sys.exit(1)
            for i in body["members"]:
                user_map[i["id"]] = i["profile"]["display_name"] if i["profile"]["display_name"] else i["real_name"]
            if (
                "response_metadata" in body
                and "next_cursor" in body["response_metadata"]
                and body["response_metadata"]["next_cursor"]
            ):
                cursor = body["response_metadata"]["next_cursor"]
            else:
                break
        return user_map

    except error.HTTPError as e:
        print(f"request FAILED: {e.code}")
        return {}
    except error.URLError as e:
        print(f"request FAILED: {e.reason}")
        return {}


def call_conversation_replies_api(ts: str) -> list:
    """
    Get all replies to the conversation specified with timestamp.
    """
    reply_list = []
    cursor = ""
    try:
        while True:
            req = setup_request(REPLY_API_PATH, args.channel_id, {"ts": ts, "cursor": cursor})
            with request.urlopen(req) as res:
                body = json.loads(res.read())
            if not body["ok"]:
                print(f'request FAILED: {body["error"]}')
                sys.exit(1)
            replies = [
                {"user": m["user"], "ts": m["ts"], "text": m["text"]} for m in body["messages"]
            ]
            reply_list.extend(replies)
            if (
                "response_metadata" in body
                and "next_cursor" in body["response_metadata"]
                and body["response_metadata"]["next_cursor"]
            ):
                cursor = body["response_metadata"]["next_cursor"]
            else:
                break
        return reply_list

    except error.HTTPError as e:
        print(f"request FAILED: {e.code}")
        return []
    except error.URLError as e:
        print(f"request FAILED: {e.reason}")
        return []


def call_conversation_history_api() -> list:
    """
    Get all conversation in the specified channel.
    """
    message_list = []
    cursor = ""
    try:
        while True:
            req = setup_request(CONVERSATION_API_PATH, args.channel_id, {"cursor": cursor})
            with request.urlopen(req) as res:
                body = json.loads(res.read())
            if not body["ok"]:
                print(f'request FAILED: {body["error"]}')
                sys.exit(1)
            messages = [
                call_conversation_replies_api(m["thread_ts"])
                if "thread_ts" in m
                else {"user": m["user"], "ts": m["ts"], "text": m["text"]}
                for m in body["messages"]
            ]
            message_list.extend(messages)
            if (
                "response_metadata" in body
                and "next_cursor" in body["response_metadata"]
                and body["response_metadata"]["next_cursor"]
            ):
                cursor = body["response_metadata"]["next_cursor"]
            else:
                break
        message_list.reverse()
        return message_list

    except error.HTTPError as e:
        print(f"request FAILED: {e.code}")
        return []
    except error.URLError as e:
        print(f"request FAILED: {e.reason}")
        return []


def output_to_file(file_path, messages):
    """
    Format and output messages to the specified file.
    """
    if os.path.isfile(file_path):
        print(
            f"{file_path} exists. Change the file to output or delete the unnecessary existing file and rerun the script. If {file_path}.tmp exists, delete it too."
        )
        sys.exit(1)

    with open(file_path, mode="a", encoding="utf_8") as f:
        for m in messages:
            if isinstance(m, dict):
                print(
                    f'{m["user"]} {convert_to_jst_dt(float(m["ts"]))}\n{m["text"]}\n\n',
                    file=f,
                )
            elif isinstance(m, list):
                for j in m:
                    if m.index(j) == 0:
                        print(
                            f'{j["user"]} {convert_to_jst_dt(float(j["ts"]))}\n{j["text"]}\n',
                            file=f,
                        )
                    elif j == m[-1]:
                        t = "\n\t".join(j["text"].splitlines())
                        print(
                            f'\t{j["user"]} {convert_to_jst_dt(float(j["ts"]))}\n\t{t}\n\n',
                            file=f,
                        )
                    else:
                        t = "\n\t".join(j["text"].splitlines())
                        print(
                            f'\t{j["user"]} {convert_to_jst_dt(float(j["ts"]))}\n\t{t}\n',
                            file=f,
                        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
            Export Slack messages including threads in the specified channel.
            You need to set environment variable SLACK_API_TOKEN first."""
    )
    parser.add_argument("channel_id", help="channel_id to export messages")
    parser.add_argument("file", help="file to output messages")
    args = parser.parse_args()

    all_messages = call_conversation_history_api()
    if len(all_messages) == 0:
        print("Failed to retrieve messages in the specified channel.")
        sys.exit(1)

    users = get_user_info()
    if len(users) == 0:
        print("Failed to retrieve user info in the workspace.")
        sys.exit(1)

    output_to_file(f"{args.file}.tmp", all_messages)
    src = Path(f"{args.file}.tmp")
    dest = Path(args.file)
    content = src.read_text("utf_8")
    for k, v in users.items():
        content = content.replace(k, v)
    dest.write_text(content, encoding="utf_8")
    os.remove(f"{args.file}.tmp")
