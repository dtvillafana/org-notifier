import orgparse as op
from orgparse import OrgNode
import os
import signal
import sys
from orgparse.node import OrgEnv
import requests
from enum import Enum
from dataclasses import dataclass


@dataclass
class Notification():
    title: str
    priority: str
    tags: str
    message: str


def send_ntfy(notification: Notification, url: str):
    resp: requests.Response = requests.post(
        url,
        data=notification.message,
        headers={
            "Title": notification.title,
            "Priority": notification.priority,
            "Tags": notification.tags,
        },
    )
    print(resp.text)


def send_notification(node: OrgNode):
    pass


def parse_file(path: str):
    org_tree_root: OrgNode = op.load(path)
    print(org_tree_root.env.todo_keys)
    print(org_tree_root.env.done_keys)


def main():
    test_file: str = "test.org"
    parse_file(path=test_file)

    pass


def test(url: str):
    send_ntfy(
        Notification(
            title="testing title",
            priority="default",
            tags="test",
            message="testing message",
        ),
        url
    )


if __name__ == "__main__":
    url: str | None = os.getenv("NTFY_URL")
    # test(url)
    main()
