from sqlalchemy.orm import declarative_base
import enum

from sqlalchemy import Column, BIGINT, VARCHAR, TIME, TIMESTAMP, INT, Enum, BINARY, func

Base = declarative_base()


class Status(enum.Enum):
    active = 1
    inactive = 2


class JobStatus(enum.Enum):
    pending = 0
    running = 1
    finished = 2
    failed = 3


class StoreTimings(Base):
    __tablename__ = "store_timings"
    id = Column("id", BIGINT, primary_key=True, autoincrement=True)
    store_id = Column("store_id", BIGINT, primary_key=False)
    day = Column("day", INT, nullable=False)
    start_time_local = Column("start_time_local", TIME, nullable=False)
    end_time_local = Column("end_time_local", TIME, nullable=False)


class StorePings(Base):
    __tablename__ = "store_pings"
    id = Column("id", BIGINT, primary_key=True, autoincrement=True)
    store_id = Column("store_id", BIGINT, nullable=False)
    status = Column("status", Enum(Status), nullable=False, default=Status.active.name)
    timestamp_utc = Column("timestamp_utc", TIMESTAMP, nullable=False)


class StoreTimezones(Base):
    __tablename__ = "store_timezones"
    store_id = Column("store_id", BIGINT, primary_key=True)
    timezone_str = Column("timezone_str", VARCHAR(255), nullable=False)


class Reports(Base):
    __tablename__ = "reports"
    report_id = Column("report_id", VARCHAR(16), primary_key=True)
    status = Column("status", Enum(JobStatus), default=JobStatus.pending.name)
    created_at = Column("created_at", TIMESTAMP, server_default=func.now())
    started_at = Column("started_at", TIMESTAMP, nullable=True)
    finished_at = Column("finished_at", TIMESTAMP, nullable=False)
    filename = Column("filename", VARCHAR(255), nullable=True)
