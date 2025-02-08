from typing import cast
import orgparse as op
import icalendar
from orgparse import OrgNode
from orgparse.node import OrgRootNode
import os
import signal
import sys
from orgparse.node import OrgEnv
import requests
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class Notification:
    title: str
    priority: str
    tags: str
    message: str


def send_ntfy(notification: Notification, url: str) -> requests.Response:
    resp: requests.Response = requests.post(
        url,
        data=notification.message,
        headers={
            "Title": notification.title,
            "Priority": notification.priority,
            "Tags": notification.tags,
        },
    )
    return resp


def node_to_notification(node: OrgNode) -> Notification:
    pass


def send_notification(node: Notification, url: str) -> requests.Response:
    resp = send_ntfy(node, url=url)
    return resp


def parse_file(path: Path) -> OrgRootNode:
    org_tree_root: OrgNode = op.load(path)
    return org_tree_root


def parse_string(orgstr: str) -> OrgRootNode:
    org_tree_root: OrgNode = op.loads(orgstr)
    return org_tree_root


def nodes_for_notification(
    time: datetime, node: OrgRootNode, reminder_intervals: list[timedelta]
) -> list[OrgNode]:
    nodes: list[OrgNode] = []
    non_empty_nodes: list[OrgNode] = list(
        filter(lambda x: x.heading.strip() != "", node)
    )
    _ = list(map(lambda x: print(x.scheduled.start), non_empty_nodes))
    # notify_now: list[OrgNode] = list(filter(lambda x: x.get))
    nodes.extend(non_empty_nodes)
    return non_empty_nodes


def main():
    test_file: Path = Path("test.org")
    test_str: str = f"""
* TODO test string node                             :testtag:
  SCHEDULED: <{datetime.now().strftime("%Y-%m-%d %a %H:%M")}> DEADLINE: <{datetime.now().strftime("%Y-%m-%d %a %H:%M")}>
"""
    org_tree_root: OrgNode = parse_string(orgstr=test_str)
    # org_tree_root: OrgNode = parse_file(path=test_file)


def test(url: str):
    test_time: datetime = datetime.now()
    test_file: Path = Path("test.org")
    test_str: str = f"""
* TODO test string node                             :testtag:
  SCHEDULED: <{test_time.strftime("%Y-%m-%d %a %H:%M")}> DEADLINE: <{(test_time + timedelta(days=1)).strftime("%Y-%m-%d %a %H:%M")}>
  body text HERE!
"""
    # org_tree_root: OrgRootNode = parse_string(orgstr=test_str)
    org_tree_root: OrgRootNode = parse_file(path=test_file)

    reminder_intervals: list[timedelta] = [timedelta(minutes=0), timedelta(days=1)]
    nodes: list[OrgNode] = nodes_for_notification(
        time=test_time, node=org_tree_root, reminder_intervals=reminder_intervals
    )
    notifications: list[Notification] = list(
        map(lambda x: node_to_notification(x), nodes)
    )
    # print(notifications)
    responses: list[requests.Response] = list(
        map(lambda x: send_notification(x, url), notifications)
    )
    # print(responses)


if __name__ == "__main__":
    url: str | None = os.getenv("NTFY_URL")
    if url:
        test(url)
    # main()
