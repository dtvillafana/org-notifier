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
    node_and_time_for_notification,
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
def test_time() -> datetime:
    return datetime.now()


@pytest.fixture
def test_org_file(temp_dir: Path, test_time: datetime) -> Path:
    org_content = f"""
* TODO Test org node 1
  SCHEDULED: <{(test_time - timedelta(weeks=1)).strftime('%Y-%m-%d %a %H:%M')} ++1w>
  body text here for test org node 1 - should notify
* TODO Test org node 2
  SCHEDULED: <{(test_time - timedelta(weeks=1)).strftime('%Y-%m-%d %a %H:%M')} ++2w>
  body text here for test org node 2 - should not notify!
* TODO Test org node 3
  SCHEDULED: <{(test_time - relativedelta(months=1)).strftime('%Y-%m-%d %a %H:%M')} ++1m>
  body text here for test org node 3 - should notify
* TODO Test org node 4
  SCHEDULED: <{(test_time - relativedelta(months=1)).strftime('%Y-%m-%d %a %H:%M')} ++2m>
  body text here for test org node 4 - should not notify!
* TODO Test org node 5
  SCHEDULED: <{(test_time - timedelta(hours=1)).strftime('%Y-%m-%d %a %H:%M')} ++1h>
  body text here for test org node 5 - should notify
* TODO Test org node 6
  SCHEDULED: <{(test_time - timedelta(hours=1)).strftime('%Y-%m-%d %a %H:%M')} ++2h>
  body text here for test org node 6 - should not notify!
* TODO Test org node 7
  SCHEDULED: <{(test_time - relativedelta(years=1)).strftime('%Y-%m-%d %a %H:%M')} ++1y>
  body text here for test org node 7 - should notify
* TODO Test org node 8
  SCHEDULED: <{(test_time - relativedelta(years=1)).strftime('%Y-%m-%d %a %H:%M')} ++2y>
  body text here for test org node 8 - should not notify!
* TODO Test org node 9
  SCHEDULED: <{(test_time - timedelta(days=1)).strftime('%Y-%m-%d %a %H:%M')} ++1d>
  body text here for test org node 9 - should notify
* TODO Test org node 10
  SCHEDULED: <{(test_time - timedelta(days=1)).strftime('%Y-%m-%d %a %H:%M')} ++2d>
  body text here for test org node 10 - should not notify!
* TODO Test org node 11
  DEADLINE: <{(test_time + timedelta(weeks=1)).strftime('%Y-%m-%d %a %H:%M')} --1w>
  body text here for test org node 11 - should not notify!
* TODO Test org node 12
  DEADLINE: <{(test_time + timedelta(weeks=1)).strftime('%Y-%m-%d %a %H:%M')} --2w>
  body text here for test org node 12 - should not notify!
* TODO Test org node 13
  DEADLINE: <{(test_time + relativedelta(months=1)).strftime('%Y-%m-%d %a %H:%M')} --1m>
  body text here for test org node 13 - should not notify!
* TODO Test org node 14
  DEADLINE: <{(test_time + relativedelta(months=1)).strftime('%Y-%m-%d %a %H:%M')} --2m>
  body text here for test org node 14 - should not notify!
* TODO Test org node 15
  DEADLINE: <{(test_time + timedelta(hours=1)).strftime('%Y-%m-%d %a %H:%M')} --1h>
  body text here for test org node 15 - should notify
* TODO Test org node 16
  DEADLINE: <{(test_time + timedelta(hours=1)).strftime('%Y-%m-%d %a %H:%M')} --2h>
  body text here for test org node 16 - should not notify!
* TODO Test org node 17
  DEADLINE: <{(test_time + relativedelta(years=1)).strftime('%Y-%m-%d %a %H:%M')} --1y>
  body text here for test org node 17 - should not notify!
* TODO Test org node 18
  DEADLINE: <{(test_time + relativedelta(years=1)).strftime('%Y-%m-%d %a %H:%M')} --2y>
  body text here for test org node 18 - should not notify!
* TODO Test org node 19
  DEADLINE: <{(test_time + timedelta(days=1)).strftime('%Y-%m-%d %a %H:%M')} --1d>
  body text here for test org node 19 - should notify
* TODO Test org node 20
  DEADLINE: <{(test_time + timedelta(days=1)).strftime('%Y-%m-%d %a %H:%M')} --2d>
  body text here for test org node 20 - should notify
* TODO Test org node 21
  SCHEDULED: <{(test_time + timedelta(days=1)).strftime('%Y-%m-%d %a %H:%M')} --3d>
  body text here for test org node 21 - should not notify!
* TODO Test org node 22
  SCHEDULED: <{(test_time + timedelta(minutes=0)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 22 - should notify
* TODO Test org node 23
  SCHEDULED: <{(test_time + timedelta(minutes=15)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 23 - should not notify
* TODO Test org node 24
  SCHEDULED: <{(test_time + timedelta(minutes=30)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 24 - should notify
* TODO Test org node 25
  SCHEDULED: <{(test_time + timedelta(minutes=45)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 25 - should not notify!
* TODO Test org node 26
  SCHEDULED: <{(test_time + timedelta(minutes=60)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 26 - should not notify!
* TODO Test org node 27
  DEADLINE: <{(test_time + timedelta(hours=6)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 27 - should notify
* TODO Test org node 28
  DEADLINE: <{(test_time + timedelta(hours=24)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 28 - should notify
* TODO Test org node 29
  DEADLINE: <{(test_time + timedelta(hours=48)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 29 - should notify
* TODO Test org node 30
  DEADLINE: <{(test_time + timedelta(hours=0)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 30 - should notify
* TODO Test org node 31
  <{(test_time + timedelta(hours=0)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 31 - should notify
* TODO Test org node 32
  <{(test_time + timedelta(minutes=30)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 32 - should notify
* TODO Test org node 33
  <{(test_time + timedelta(minutes=25)).strftime('%Y-%m-%d %a %H:%M')}>
  <{(test_time + timedelta(minutes=30)).strftime('%Y-%m-%d %a %H:%M')}>
  <{(test_time + timedelta(minutes=50)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 33 - should notify
* TODO Test org node 34
  <{(test_time + timedelta(minutes=25)).strftime('%Y-%m-%d %a %H:%M')}>
  <{(test_time + timedelta(minutes=31)).strftime('%Y-%m-%d %a %H:%M')}>
  <{(test_time + timedelta(minutes=50)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 34 - should not notify
* TODO Test org node 35
  [{(test_time + timedelta(minutes=0)).strftime('%Y-%m-%d %a %H:%M')}]
  [{(test_time + timedelta(minutes=15)).strftime('%Y-%m-%d %a %H:%M')}]
  [{(test_time + timedelta(minutes=30)).strftime('%Y-%m-%d %a %H:%M')}]
  body text here for test org node 35 - should not notify
* DONE Test org node 36
  <{(test_time + timedelta(minutes=0)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 36 - should not notify
* DONE Test org node 37
  SCHEDULED: <{(test_time + timedelta(minutes=0)).strftime('%Y-%m-%d %a %H:%M')}>
  body text here for test org node 37 - should not notify
"""
    file_path = temp_dir / "test.org"
    _ = file_path.write_text(org_content)
    return file_path


@pytest.fixture
def test_early_notification_bug(temp_dir: Path) -> Path:
    test_time: datetime = datetime(year=2025, month=2, day=14)
    org_content: str = f"""
* TODO Test bug org node 1
  SCHEDULED: <{(test_time).strftime('%Y-%m-%d %a')} 11:30>
  body text here for test org node 1 - should not notify
"""
    file_path = temp_dir / "notif_bug.org"
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
    assert len(get_valid_nodes(node)) == 37


def test_node_for_notification(test_org_file: Path, test_time: datetime):
    org_tree_root: OrgRootNode = parse_file(path=test_org_file)
    valid_nodes: list[OrgNode] = get_valid_nodes(org_tree_root)
    [print(f"{ x.heading }, { x.datelist }, { x.has_date() }") for x in valid_nodes]
    intervals: dict[str, list[timedelta]] = {
        "scheduled": generate_scheduled_notification_intervals(),
        "deadline": generate_deadline_notification_intervals(),
    }
    nodes: list[tuple[OrgNode, datetime]] = node_and_time_for_notification(
        time=test_time, node=org_tree_root, reminder_intervals=intervals
    )
    assert any("Test org node 1" == node[0].heading for node in nodes)
    assert not any("Test org node 2" == node[0].heading for node in nodes)
    assert any("Test org node 3" == node[0].heading for node in nodes)
    assert not any("Test org node 4" == node[0].heading for node in nodes)
    assert any("Test org node 5" == node[0].heading for node in nodes)
    assert not any("Test org node 6" == node[0].heading for node in nodes)
    assert any("Test org node 7" == node[0].heading for node in nodes)
    assert not any("Test org node 8" == node[0].heading for node in nodes)
    assert any("Test org node 9" == node[0].heading for node in nodes)
    assert not any("Test org node 10" == node[0].heading for node in nodes)
    assert not any("Test org node 11" == node[0].heading for node in nodes)
    assert not any("Test org node 12" == node[0].heading for node in nodes)
    assert not any("Test org node 13" == node[0].heading for node in nodes)
    assert not any("Test org node 14" == node[0].heading for node in nodes)
    assert any("Test org node 15" == node[0].heading for node in nodes)
    assert not any("Test org node 16" == node[0].heading for node in nodes)
    assert not any("Test org node 17" == node[0].heading for node in nodes)
    assert not any("Test org node 18" == node[0].heading for node in nodes)
    assert any("Test org node 19" == node[0].heading for node in nodes)
    assert any("Test org node 20" == node[0].heading for node in nodes)
    assert not any("Test org node 21" == node[0].heading for node in nodes)
    assert any("Test org node 22" == node[0].heading for node in nodes)
    assert any("Test org node 23" == node[0].heading for node in nodes)
    assert any("Test org node 24" == node[0].heading for node in nodes)
    assert not any("Test org node 25" == node[0].heading for node in nodes)
    assert not any("Test org node 26" == node[0].heading for node in nodes)
    assert any("Test org node 27" == node[0].heading for node in nodes)
    assert any("Test org node 28" == node[0].heading for node in nodes)
    assert any("Test org node 29" == node[0].heading for node in nodes)
    assert any("Test org node 30" == node[0].heading for node in nodes)
    assert any("Test org node 31" == node[0].heading for node in nodes)
    assert any("Test org node 32" == node[0].heading for node in nodes)
    assert any("Test org node 33" == node[0].heading for node in nodes)
    assert not any("Test org node 34" == node[0].heading for node in nodes)
    assert not any("Test org node 35" == node[0].heading for node in nodes)
    assert not any("Test org node 36" == node[0].heading for node in nodes)
    assert not any("Test org node 37" == node[0].heading for node in nodes)


def test_notification_bug(test_early_notification_bug: Path):
    test_time: datetime = datetime(year=2025, month=2, day=13, hour=23, minute=30)
    org_tree_root: OrgRootNode = parse_file(path=test_early_notification_bug)
    intervals: dict[str, list[timedelta]] = {
        "scheduled": generate_scheduled_notification_intervals(),
        "deadline": generate_deadline_notification_intervals(),
    }
    nodes: list[tuple[OrgNode, datetime]] = node_and_time_for_notification(
        time=test_time, node=org_tree_root, reminder_intervals=intervals
    )
    valid_nodes = get_valid_nodes(org_tree_root)
    assert len(valid_nodes) == 1
    print(valid_nodes)
    assert not any("Test bug org node 1" == node[0].heading for node in nodes)
