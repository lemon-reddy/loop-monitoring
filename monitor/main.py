import zoneinfo
from datetime import datetime, timedelta, time
from dataclasses import dataclass
from itertools import islice
import tempfile
import csv

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.exc import NoResultFound
from uuid import uuid4
from .model import Reports, StoreTimezones, StorePings, StoreTimings
from .session import db_session as session, redis_session
from sqlalchemy import desc, update
from .utils import check_exists
from .constants import REDIS_STORE_IDS, REDIS_TIMEZONES


router = APIRouter()


start_time = datetime(year=2023, month=1, day=23, hour=17)


@dataclass
class StoreStatus:
    active_hour: int
    inactive_hour: int
    active_day: int
    inactive_day: int
    active_week: int
    inactive_week: int


@dataclass
class LocalPing:
    status: str
    local_time: datetime


machine_user_text = {
    "active_hour": "uptime_last_hour(in minutes)",
    "inactive_hour": "downtime_last_hour(in minutes)",
    "active_day": "uptime_last_day(in hours)",
    "inactive_day": "downtime_last_day(in hours)",
    "active_week": "uptime_last_week(in hours)",
    "inactive_week": "downtime_last_week(in hours)",
}


def cache_timezones():
    all_zones = session.query(
        StoreTimezones.store_id, StoreTimezones.timezone_str
    ).all()
    zone_map = {}
    for zone in all_zones:
        zone_map.update({zone.store_id: zone.timezone_str})
    print(f"Reached here. {len(zone_map)}")
    redis_session.hmset(REDIS_TIMEZONES, zone_map)
    return zone_map


def get_timezones():
    if check_exists(redis_key=REDIS_STORE_IDS):
        return redis_session.hgetall(REDIS_TIMEZONES)
    else:
        return cache_timezones()


def last_hour_status(pings: list[LocalPing], current_time, timings):
    last_hour = {"active": timedelta(seconds=0), "inactive": timedelta(seconds=0)}
    latest_status = None
    for ping in pings[:2]:
        if not valid_ping(ping, timings=timings):
            continue
        elif (ping.local_time - current_time) < timedelta(hours=1):
            latest_status = ping.status
            last_hour[ping.status.name] += ping.local_time - current_time
        elif (
            (ping.local_time - current_time) < timedelta(hours=2)
            and (ping.status != latest_status)
            and (current_time - timedelta(minutes=90) < ping.local_time)
        ):
            last_hour[ping.status.name] = (
                ping.local_time + timedelta(minutes=90) - current_time
            )
            last_hour[latest_status] += timedelta(minutes=30)
        else:
            last_hour[ping.status.name] = timedelta(hours=1)
    active_time = last_hour["active"].total_seconds() / 60
    inactive_time = last_hour["inactive"].total_seconds() / 60
    return active_time, inactive_time


def valid_ping(ping, timings):
    weekday = ping.local_time.weekday()
    if timings.get(weekday):
        temp_start_time = timings[weekday][0]
        temp_end_time = timings[weekday][1]
    else:
        temp_start_time = time.min
        temp_end_time = time.max
    day_time = ping.local_time.time()
    if day_time < temp_start_time or day_time > temp_end_time:
        return False
    return True


def cumulative_status(pings: list[LocalPing], timings, current_time):
    last_week_counts = {"active": 0, "inactive": 0}
    last_day_counts = {"active": 0, "inactive": 0}
    for ping in pings:
        if not valid_ping(ping, timings=timings):
            continue
        if ping.local_time > current_time - timedelta(days=1):
            last_day_counts[ping.status.name] += 1
        last_week_counts[ping.status.name] += 1
    active_week = last_week_counts["active"]
    inactive_week = last_week_counts["inactive"]
    active_day = last_day_counts["active"]
    inactive_day = last_day_counts["inactive"]
    return active_day, inactive_day, active_week, inactive_week


def calculate_times(pings, timings, current_time):
    active_hour, inactive_hour = last_hour_status(
        pings=pings, current_time=current_time, timings=timings
    )
    active_day, inactive_day, active_week, inactive_week = cumulative_status(
        pings=pings, timings=timings, current_time=current_time
    )
    return [
        active_hour,
        inactive_hour,
        active_day,
        inactive_day,
        active_week,
        inactive_week,
    ]


def store_report(pings, timings, timezone, current_time):
    local_pings = []
    for ping in pings:
        local_pings.append(
            LocalPing(
                status=ping.status,
                local_time=ping.timestamp_utc.astimezone(zoneinfo.ZoneInfo(timezone)),
            )
        )
    return calculate_times(
        pings=local_pings,
        timings=timings,
        current_time=current_time.astimezone(zoneinfo.ZoneInfo(timezone)),
    )


def bulk_store_report(timezones: dict, current_time) -> list[StoreStatus]:
    store_ids = timezones.keys()
    pings = (
        session.query(StorePings.status, StorePings.timestamp_utc, StorePings.store_id)
        .filter(StorePings.store_id.in_(store_ids))
        .filter(StorePings.timestamp_utc > timedelta(days=7))
        .order_by(StorePings.store_id, desc(StorePings.timestamp_utc))
        .all()
    )
    timings = (
        session.query(
            StoreTimings.start_time_local,
            StoreTimings.end_time_local,
            StoreTimings.day,
            StoreTimings.store_id,
        )
        .filter(StoreTimings.store_id.in_(store_ids))
        .order_by(StoreTimings.store_id, StoreTimings.day)
        .all()
    )
    if not pings or not timings:
        return []
    store_timings = {}
    for timing in timings:
        if not store_timings.get(timing.store_id):
            store_timings[timing.store_id] = {}
        store_timings[timing.store_id][timing.day] = (
            timing.start_time_local,
            timing.end_time_local,
        )
    prev_store_id = None
    store_pings = []
    bulk_reports = []
    for ping in pings:
        if ping.store_id != prev_store_id and prev_store_id != None:
            bulk_reports.append(
                [
                    prev_store_id,
                    *store_report(
                        store_pings,
                        timezone=timezones[prev_store_id],
                        timings=store_timings.get(prev_store_id, {}),
                        current_time=current_time,
                    ),
                ]
            )
            store_pings = []
        else:
            store_pings.append(ping)
        prev_store_id = ping.store_id
    bulk_reports.append(
        store_report(
            store_pings,
            timezone=timezones[prev_store_id],
            timings=store_timings.get(prev_store_id, {}),
            current_time=current_time,
        )
    )
    return bulk_reports


def chunk_timezones(timezones, chunk_size=100):
    it = iter(timezones)
    for idx in range(0, len(timezones), chunk_size):
        yield {k: timezones[k] for k in islice(it, chunk_size)}


def convert_csv(final_reports, report_id):
    with tempfile.NamedTemporaryFile(
        suffix=f"_{report_id}.csv", delete=False
    ) as csvfile:
        writer = csv.writer(
            csvfile,
        )
        writer.writerow(["store_id", *list(machine_user_text.values())])
        writer.writerows(final_reports)
        return csvfile.name


def generate_report(report_id, chunk_size=100):
    update_report_status(report_id=report_id, status="running")
    current_time = start_time  # Should be substituted with datetime.utcnow()
    final_report = []
    for chunked_zones in chunk_timezones(
        timezones=get_timezones(), chunk_size=chunk_size
    ):
        final_report.extend(
            bulk_store_report(timezones=chunked_zones, current_time=current_time)
        )
    filename = convert_csv(final_report)
    update_report_status(report_id=report_id, status="finished", filename=filename)


def update_report_status(report_id, status, filename=None):
    update_values = {"status": status, "filename": filename}
    if status == "running":
        update_values["started_time"] = datetime.utcnow()
    elif status == "finished":
        update_values["finished_time"] = datetime.utcnow()
    update_instance = (
        update(Reports).where(Reports.report_id == report_id).values(**update_values)
    )
    session.execute(update_instance)
    session.commit()


def store_status_csv(final_report):
    return


@router.post(
    "/trigger_report",
)
async def trigger_report(background_tasks: BackgroundTasks):
    report_id = uuid4()
    report = Reports(
        report_id=report_id, status="pending", created_at=datetime.utcnow()
    )
    session.add(report)
    session.commit()
    background_tasks.add_task(generate_report, report_id)
    return JSONResponse({"report_id": report_id})


@router.get("/get_report/{report_id}")
async def get_report(report_id: int):
    try:
        report = (
            session.query(Reports.filename).filter(Reports.report_id == report_id).one()
        )
        return FileResponse(
            path=report.filename,
            media_type="text/csv",
            filename=f"report_{report_id}.csv",
        )
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"Report_id {report_id} not found.")
    return
