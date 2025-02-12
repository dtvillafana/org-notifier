from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Generator
from dateutil.relativedelta import relativedelta
import pytest
from orgparse.node import OrgNode, OrgRootNode
from src.main import (
    Config,
    generate_deadline_notification_intervals,
    generate_scheduled_notification_intervals,
    get_valid_nodes,
    nodes_for_notification,
    parse_file,
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    path = Path("test_temp/")
    path.mkdir()
    yield path
    # Cleanup happens automatically after tests
    from shutil import rmtree

    rmtree(path)


@pytest.fixture
def ntfy_url() -> str:
    return str(os.getenv("NTFY_URL"))


@pytest.fixture
def now() -> datetime:
    return datetime.now()


@pytest.fixture
def test_org_file(temp_dir: Path) -> Path:
    now = datetime.now()
    org_content = f"""
* TODO Test org node 1
  SCHEDULED: <{(now - timedelta(weeks=1)).strftime('%Y-%m-%d %a %H:%M')} ++1w>
  body text here for test org node 1 - should notify
* TODO Test org node 2
  SCHEDULED: <{(now - timedelta(weeks=1)).strftime('%Y-%m-%d %a %H:%M')} ++2w>
  body text here for test org node 2 - should not notify!
* TODO Test org node 3
  SCHEDULED: <{(now - relativedelta(months=1)).strftime('%Y-%m-%d %a %H:%M')} ++1m>
  body text here for test org node 3 - should notify
* TODO Test org node 4
  SCHEDULED: <{(now - relativedelta(months=1)).strftime('%Y-%m-%d %a %H:%M')} ++2m>
  body text here for test org node 4 - should not notify!
* TODO Test org node 5
  SCHEDULED: <{(now - timedelta(hours=1)).strftime('%Y-%m-%d %a %H:%M')} ++1h>
  body text here for test org node 5 - should notify
* TODO Test org node 6
  SCHEDULED: <{(now - timedelta(hours=1)).strftime('%Y-%m-%d %a %H:%M')} ++2h>
  body text here for test org node 6 - should not notify!
* TODO Test org node 7
  SCHEDULED: <{(now - relativedelta(years=1)).strftime('%Y-%m-%d %a %H:%M')} ++1y>
  body text here for test org node 7 - should notify
* TODO Test org node 8
  SCHEDULED: <{(now - relativedelta(years=1)).strftime('%Y-%m-%d %a %H:%M')} ++2y>
  body text here for test org node 8 - should not notify!
* TODO Test org node 9
  SCHEDULED: <{(now - timedelta(days=1)).strftime('%Y-%m-%d %a %H:%M')} ++1d>
  body text here for test org node 9 - should notify
* TODO Test org node 10
  SCHEDULED: <{(now - timedelta(days=1)).strftime('%Y-%m-%d %a %H:%M')} ++2d>
  body text here for test org node 10 - should not notify!
* TODO Test org node 11
  DEADLINE: <{(now + timedelta(weeks=1)).strftime('%Y-%m-%d %a %H:%M')} --1w>
  body text here for test org node 11 - should not notify!
* TODO Test org node 12
  DEADLINE: <{(now + timedelta(weeks=1)).strftime('%Y-%m-%d %a %H:%M')} --2w>
  body text here for test org node 12 - should not notify!
* TODO Test org node 13
  DEADLINE: <{(now + relativedelta(months=1)).strftime('%Y-%m-%d %a %H:%M')} --1m>
  body text here for test org node 13 - should not notify!
* TODO Test org node 14
  DEADLINE: <{(now + relativedelta(months=1)).strftime('%Y-%m-%d %a %H:%M')} --2m>
  body text here for test org node 14 - should not notify!
* TODO Test org node 15
  DEADLINE: <{(now + timedelta(hours=1)).strftime('%Y-%m-%d %a %H:%M')} --1h>
  body text here for test org node 15 - should notify
* TODO Test org node 16
  DEADLINE: <{(now + timedelta(hours=1)).strftime('%Y-%m-%d %a %H:%M')} --2h>
  body text here for test org node 16 - should not notify!
* TODO Test org node 17
  DEADLINE: <{(now + relativedelta(years=1)).strftime('%Y-%m-%d %a %H:%M')} --1y>
  body text here for test org node 17 - should not notify!
* TODO Test org node 18
  DEADLINE: <{(now + relativedelta(years=1)).strftime('%Y-%m-%d %a %H:%M')} --2y>
  body text here for test org node 18 - should not notify!
* TODO Test org node 19
  DEADLINE: <{(now + timedelta(days=1)).strftime('%Y-%m-%d %a %H:%M')} --1d>
  body text here for test org node 19 - should notify
* TODO Test org node 20
  DEADLINE: <{(now + timedelta(days=1)).strftime('%Y-%m-%d %a %H:%M')} --2d>
  body text here for test org node 20 - should notify
* TODO Test org node 21
  SCHEDULED: <{(now + timedelta(days=1)).strftime('%Y-%m-%d %a %H:%M')} --3d>
  body text here for test org node 21 - should not notify!
* TODO Test org node 22
  SCHEDULED: <{(now + timedelta(minutes=0)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 22 - should notify
* TODO Test org node 23
  SCHEDULED: <{(now + timedelta(minutes=15)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 23 - should not notify
* TODO Test org node 24
  SCHEDULED: <{(now + timedelta(minutes=30)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 24 - should notify
* TODO Test org node 25
  SCHEDULED: <{(now + timedelta(minutes=45)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 25 - should not notify!
* TODO Test org node 26
  SCHEDULED: <{(now + timedelta(minutes=60)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 26 - should not notify!
* TODO Test org node 27
  DEADLINE: <{(now + timedelta(hours=6)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 27 - should notify
* TODO Test org node 28
  DEADLINE: <{(now + timedelta(hours=24)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 28 - should notify
* TODO Test org node 29
  DEADLINE: <{(now + timedelta(hours=48)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 29 - should notify
* TODO Test org node 30
  DEADLINE: <{(now + timedelta(hours=0)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 30 - should notify
"""
    file_path = temp_dir / "test.org"
    _ = file_path.write_text(org_content)
    return file_path


@pytest.fixture
def config(temp_dir: Path, ntfy_url: str) -> Config:
    return Config(
        base_dir=temp_dir,
        reminder_intervals=generate_scheduled_notification_intervals(),
        ntfy_url=ntfy_url,
    )


def test_parse_file(test_org_file: Path):
    node = parse_file(path=test_org_file)
    assert isinstance(node, OrgRootNode)


def test_get_valid_nodes(test_org_file: Path):
    node = parse_file(path=test_org_file)
    assert len(get_valid_nodes(node)) == 30


def test_node_for_notification(test_org_file: Path, now: datetime):
    org_tree_root: OrgRootNode = parse_file(path=test_org_file)
    intervals: dict[str, list[timedelta]] = {
        "scheduled": generate_scheduled_notification_intervals(),
        "deadline": generate_deadline_notification_intervals(),
    }
    nodes: list[OrgNode] = nodes_for_notification(
        time=now, node=org_tree_root, reminder_intervals=intervals
    )
    assert any("Test org node 1" == node.heading for node in nodes)
    assert not any("Test org node 2" == node.heading for node in nodes)
    assert any("Test org node 3" == node.heading for node in nodes)
    assert not any("Test org node 4" == node.heading for node in nodes)
    assert any("Test org node 5" == node.heading for node in nodes)
    assert not any("Test org node 6" == node.heading for node in nodes)
    assert any("Test org node 7" == node.heading for node in nodes)
    assert not any("Test org node 8" == node.heading for node in nodes)
    assert any("Test org node 9" == node.heading for node in nodes)
    assert not any("Test org node 10" == node.heading for node in nodes)
    assert not any("Test org node 11" == node.heading for node in nodes)
    assert not any("Test org node 12" == node.heading for node in nodes)
    assert not any("Test org node 13" == node.heading for node in nodes)
    assert not any("Test org node 14" == node.heading for node in nodes)
    assert any("Test org node 15" == node.heading for node in nodes)
    assert not any("Test org node 16" == node.heading for node in nodes)
    assert not any("Test org node 17" == node.heading for node in nodes)
    assert not any("Test org node 18" == node.heading for node in nodes)
    assert any("Test org node 19" == node.heading for node in nodes)
    assert any("Test org node 20" == node.heading for node in nodes)
    assert not any("Test org node 21" == node.heading for node in nodes)
    assert any("Test org node 22" == node.heading for node in nodes)
    assert any("Test org node 23" == node.heading for node in nodes)
    assert any("Test org node 24" == node.heading for node in nodes)
    assert not any("Test org node 25" == node.heading for node in nodes)
    assert not any("Test org node 26" == node.heading for node in nodes)
    assert any("Test org node 27" == node.heading for node in nodes)
    assert any("Test org node 28" == node.heading for node in nodes)
    assert any("Test org node 29" == node.heading for node in nodes)
    assert any("Test org node 30" == node.heading for node in nodes)
