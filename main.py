import json
from typing import Any
import orgparse as op
from orgparse.node import OrgNode
from orgparse.node import OrgRootNode
import os
import requests
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from pathlib import Path


@dataclass
class Notification:
    title: str
    priority: str
    tags: str
    message: str
    time: str


@dataclass
class Config:
    base_dir: Path
    reminder_intervals: list[timedelta] | None
    ntfy_url: str

    def __bool__(self):
        return bool(
            self.base_dir.exists() and self.reminder_intervals and self.ntfy_url
        )


def generate_notification_intervals() -> list[timedelta]:
    return [timedelta(minutes=0), timedelta(minutes=15), timedelta(minutes=30)]


def send_ntfy(notification: Notification, url: str) -> requests.Response:
    resp: requests.Response = requests.post(
        url,
        data=notification.message,
        headers={
            "Title": f"{notification.title} @ {notification.time}",
            "Priority": notification.priority,
            "Tags": notification.tags,
        },
    )
    return resp


def node_to_notification(node: OrgNode) -> Notification:
    priority_map: dict[str | None, str] = {"A": "urgent", None: "default"}
    return Notification(
        title=node.heading,
        priority=priority_map[node.priority],
        tags=",".join(node.tags),
        message=node.body if node.body.strip() else node.heading,
        time=f'({node.scheduled.start.strftime("%Y-%m-%d %H:%M")})',
    )


def send_notification(node: Notification, url: str) -> requests.Response:
    resp = send_ntfy(node, url=url)
    return resp


def parse_file(path: Path) -> OrgRootNode:
    org_tree_root: OrgRootNode = op.load(path)
    return org_tree_root


def parse_string(orgstr: str) -> OrgRootNode:
    org_tree_root: OrgRootNode = op.loads(orgstr)
    return org_tree_root


def coerce_datetime(d: date | datetime):
    if isinstance(d, datetime):
        return d
    if isinstance(d, date):
        return datetime.combine(d, datetime.min.time())
    raise TypeError(f"Can't convert {type(d)} to datetime")


def nodes_for_notification(
    time: datetime, node: OrgRootNode, reminder_intervals: list[timedelta]
) -> list[OrgNode]:
    nodes: list[OrgNode] = []
    non_empty_nodes: list[OrgNode] = list(
        filter(lambda x: x.heading.strip() != "", node)
    )
    notification_precise_times: list[datetime] = list(
        map(lambda x: time + x, reminder_intervals)
    )
    notification_times: list[datetime] = list(
        map(
            lambda x: coerce_datetime(x).replace(second=0, microsecond=0),
            notification_precise_times,
        )
    )
    nodes_for_notification: list[OrgNode] = list(
        filter(
            lambda x: coerce_datetime(x.scheduled.start).replace(
                second=0, microsecond=0
            )
            in notification_times,
            filter(
                lambda x: x.scheduled.start is not None,
                non_empty_nodes,
            ),
        )
    )
    return nodes_for_notification


def parse_and_send(file: Path, time: datetime, url: str) -> list[requests.Response]:
    org_tree_root: OrgRootNode = parse_file(path=file)

    reminder_intervals: list[timedelta] = generate_notification_intervals()
    nodes: list[OrgNode] = nodes_for_notification(
        time=time, node=org_tree_root, reminder_intervals=reminder_intervals
    )
    notifications: list[Notification] = list(
        map(lambda x: node_to_notification(x), nodes)
    )
    return list(map(lambda x: send_notification(x, url), notifications))


def load_config(org_basedir: str, url: str) -> Config:
    config_path: Path = Path(org_basedir) / ".org-notifier-config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            json_config: dict[str, Any] | None = json.load(f)
        return Config(
            base_dir=Path(org_basedir),
            reminder_intervals=json_config.get("reminder_intervals", []),
            ntfy_url=url,
        )
    else:
        return Config(
            base_dir=Path(org_basedir),
            reminder_intervals=generate_notification_intervals(),
            ntfy_url=url,
        )


def main(url: str, org_basedir: str):
    # load config
    config: Config = load_config(org_basedir=org_basedir, url=url)
    if config:
        org_files: list[Path] = list(
            filter(
                lambda x: x.is_file() and x.name.endswith(".org"),
                config.base_dir.glob("**/*"),
            )
        )
        now: datetime = datetime.now()
        _ = list(
            map(
                lambda x: parse_and_send(file=x, time=now, url=config.ntfy_url),
                org_files,
            )
        )


if __name__ == "__main__":
    url: str | None = os.getenv("NTFY_URL")
    org_basedir: str | None = os.getenv("ORG_BASEDIR")
    if url and org_basedir:
        main(url, org_basedir)
    else:
        raise Exception(
            f'Supply environment variable(s): {None if url else "url"} {None if org_basedir else "org_basedir"}'
        )
