import json
from typing import Any
import orgparse as op
from orgparse.node import OrgNode
from orgparse.node import OrgRootNode
import os
import requests
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from pathlib import Path
import itertools


@dataclass
class Notification:
    title: str
    priority: str
    tags: str
    message: str
    time: datetime


@dataclass
class Config:
    base_dir: Path
    reminder_intervals: list[timedelta] | None
    ntfy_url: str

    def __bool__(self):
        return bool(
            self.base_dir.exists() and self.reminder_intervals and self.ntfy_url
        )


def flatmap(list_of_lists: list[list[Any]]) -> list[Any]:
    return list(itertools.chain.from_iterable(list_of_lists))


def generate_scheduled_notification_intervals() -> list[timedelta]:
    return [timedelta(minutes=0), timedelta(minutes=15), timedelta(minutes=30)]


def generate_deadline_notification_intervals() -> list[timedelta]:
    return [
        timedelta(minutes=0),
        timedelta(hours=6),
        timedelta(hours=12),
        timedelta(hours=24),
        timedelta(hours=48),
    ]


def send_ntfy(
    notification: Notification, url: str, time: datetime
) -> requests.Response:
    minutes_until: int = int((notification.time - time).total_seconds() // 60)
    resp: requests.Response = requests.post(
        url,
        data=notification.message,
        headers={
            "Title": f"{notification.title} {f'(in {abs(minutes_until)} minutes)' if minutes_until > 1 else '(now)'}",
            "Priority": notification.priority,
            "Tags": notification.tags,
        },
    )
    return resp


def generate_notification(node: OrgNode, time: datetime) -> Notification:
    priority_map: dict[str | None, str] = {"A": "urgent", None: "default"}
    return Notification(
        title=node.heading,
        priority=priority_map[node.priority],
        tags=",".join(node.tags),
        message=node.body if node.body.strip() else node.heading,
        time=time,
    )


def send_notification(
    node: Notification, url: str, time: datetime
) -> requests.Response:
    resp = send_ntfy(notification=node, url=url, time=time)
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


def repeater_to_interval(repeater: tuple[str, int, str]) -> timedelta | relativedelta:
    interval_value: int = repeater[1]
    interval: str = repeater[2]
    match interval.lower():
        case "y":
            return relativedelta(years=interval_value)
        case "m":
            return relativedelta(months=interval_value)
        case "w":
            return timedelta(weeks=interval_value)
        case "d":
            return timedelta(days=interval_value)
        case "h":
            return timedelta(hours=interval_value)
        case _:
            raise ValueError(
                f"Invalid interval: {interval}, Must be one of: y, m, w, d, h"
            )


def is_in_series(
    series_basis: datetime,
    interval: timedelta | relativedelta,
    check_dates: list[datetime],
) -> bool:
    # Normalize times by removing seconds and microseconds
    series_basis = series_basis.replace(second=0, microsecond=0)
    check_dates = [d.replace(second=0, microsecond=0) for d in check_dates]

    if isinstance(interval, timedelta):
        # Convert to minutes for integer arithmetic
        interval_minutes = int(interval.total_seconds() // 60)

        for check_date in check_dates:
            # Calculate time difference in minutes
            diff = check_date - series_basis
            diff_minutes = int(diff.total_seconds() // 60)

            # Skip negative differences
            if diff_minutes < 0:
                continue

            # Check if it's an exact multiple
            if diff_minutes % interval_minutes == 0:
                return True

        return False
    else:
        # For relativedelta, precompute a reasonable number of occurrences
        # This is still faster than the original while loop approach
        occurrences: set[datetime] = set()
        current = series_basis

        # Calculate max difference to determine how many iterations we need
        max_check_date = max(check_dates)

        while current <= max_check_date:
            occurrences.add(current)
            current += interval

        # Check if any of our check_dates are in the occurrences
        return any(d in occurrences for d in check_dates)


def get_valid_nodes(node: OrgRootNode) -> list[OrgNode]:
    org_nodes: list[OrgNode] = list(node[1:])
    valid_nodes: list[OrgNode] = list(
        filter(lambda x: x.heading.strip() != "", org_nodes)
    )
    return valid_nodes


def node_and_time_for_notification(
    time: datetime, node: OrgRootNode, reminder_intervals: dict[str, list[timedelta]]
) -> list[tuple[OrgNode, datetime]]:
    """The reason we return a list of tuples here instead of just the node is because the generate notification function needs a time in the notification"""
    valid_nodes: list[OrgNode] = get_valid_nodes(node)
    scheduled_notification_precise_times: list[datetime] = list(
        map(lambda x: time + x, reminder_intervals["scheduled"])
    )
    deadline_notification_precise_times: list[datetime] = list(
        map(lambda x: time + x, reminder_intervals["deadline"])
    )
    scheduled_notification_times: list[datetime] = list(
        map(
            lambda x: coerce_datetime(x).replace(second=0, microsecond=0),
            scheduled_notification_precise_times,
        )
    )
    deadline_notification_times: list[datetime] = list(
        map(
            lambda x: coerce_datetime(x).replace(second=0, microsecond=0),
            deadline_notification_precise_times,
        )
    )
    matching_plain_timestamp_nodes: list[tuple[OrgNode, datetime]] = list(
        map(
            lambda x: (
                x,
                coerce_datetime(
                    min(
                        filter(
                            lambda x: coerce_datetime(x.start).replace(
                                second=0, microsecond=0
                            )
                            in scheduled_notification_times,
                            x.get_timestamps(active=True, range=True, point=True),
                        ),
                        key=lambda x: coerce_datetime(x.start),
                    ).start
                ),
            ),
            filter(
                lambda x: any(
                    coerce_datetime(y.start).replace(second=0, microsecond=0)
                    in scheduled_notification_times
                    for y in x.get_timestamps(active=True, range=True, point=True)
                ),
                filter(
                    lambda x: x.get_timestamps(active=True, range=True, point=True),
                    filter(
                        lambda x: x._todo not in x.env.done_keys,
                        valid_nodes,
                    ),
                ),
            ),
        )
    )
    matching_scheduled_nodes: list[tuple[OrgNode, datetime]] = list(
        map(
            lambda x: (x, coerce_datetime(x.scheduled.start)),
            filter(
                lambda x: coerce_datetime(x.scheduled.start).replace(
                    second=0, microsecond=0
                )
                in scheduled_notification_times,
                filter(
                    lambda x: x.scheduled.start is not None
                    and x.scheduled._repeater is None,
                    filter(
                        lambda x: x._todo not in x.env.done_keys,
                        valid_nodes,
                    ),
                ),
            ),
        )
    )
    matching_deadline_nodes: list[tuple[OrgNode, datetime]] = list(
        map(
            lambda x: (x, coerce_datetime(x.deadline.start)),
            filter(
                lambda x: coerce_datetime(x.deadline.start).replace(
                    second=0, microsecond=0
                )
                in deadline_notification_times,
                filter(
                    lambda x: x.deadline.start is not None
                    and x.deadline._warning is None,
                    filter(
                        lambda x: x._todo not in x.env.done_keys,
                        valid_nodes,
                    ),
                ),
            ),
        )
    )
    matching_deadline_only_warning_nodes: list[tuple[OrgNode, datetime]] = list(
        map(
            lambda x: (x, coerce_datetime(x.deadline.start)),
            filter(
                lambda x: is_in_series(
                    series_basis=coerce_datetime(x.deadline.start),
                    interval=-repeater_to_interval(x.deadline._warning),
                    check_dates=deadline_notification_times,
                )
                == True,
                filter(
                    lambda x: (x.deadline._warning is not None)
                    and (x.deadline._repeater is None),
                    filter(
                        lambda x: x._todo not in x.env.done_keys,
                        valid_nodes,
                    ),
                ),
            ),
        )
    )
    matching_scheduled_only_repeater_nodes: list[tuple[OrgNode, datetime]] = list(
        map(
            lambda x: (
                x,
                coerce_datetime(x.scheduled.start).replace(
                    year=time.year, month=time.month, day=time.day
                ),
            ),
            filter(
                lambda x: is_in_series(
                    series_basis=coerce_datetime(x.scheduled.start),
                    interval=repeater_to_interval(x.scheduled._repeater),
                    check_dates=scheduled_notification_times,
                )
                == True,
                filter(
                    lambda x: x.scheduled._repeater is not None,
                    filter(lambda x: x._todo not in x.env.done_keys, valid_nodes),
                ),
            ),
        )
    )
    all_matching_nodes: list[tuple[OrgNode, datetime]] = (
        matching_scheduled_only_repeater_nodes
        + matching_scheduled_nodes
        + matching_deadline_nodes
        + matching_deadline_only_warning_nodes
        + matching_plain_timestamp_nodes
    )
    return all_matching_nodes


def parse_and_send(file: Path, time: datetime, url: str) -> list[requests.Response]:
    org_tree_root: OrgRootNode = parse_file(path=file)

    intervals: dict[str, list[timedelta]] = {
        "scheduled": generate_scheduled_notification_intervals(),
        "deadline": generate_deadline_notification_intervals(),
    }
    nodes: list[tuple[OrgNode, datetime]] = node_and_time_for_notification(
        time=time, node=org_tree_root, reminder_intervals=intervals
    )
    notifications: list[Notification] = list(
        map(lambda x: generate_notification(x[0], x[1]), nodes)
    )
    return list(map(lambda x: send_notification(x, url, time), notifications))


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
            reminder_intervals=generate_scheduled_notification_intervals(),
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
        responses: list[list[requests.Response]] = flatmap(
            list(
                map(
                    lambda x: parse_and_send(file=x, time=now, url=config.ntfy_url),
                    org_files,
                )
            )
        )
        print([x.text for x in responses])


if __name__ == "__main__":
    url: str | None = os.getenv("NTFY_URL")
    org_basedir: str | None = os.getenv("ORG_BASEDIR")
    if url and org_basedir:
        main(url, org_basedir)
    else:
        raise Exception(
            f'Supply environment variable(s): {None if url else "url"} {None if org_basedir else "org_basedir"}'
        )
