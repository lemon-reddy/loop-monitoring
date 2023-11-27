from . import read_csv
from monitor.model import StorePings
from monitor.session import db_session as session


def seed_store_timings(filename="store_status.csv"):
    for chunk_data in read_csv(filename=filename, window_size=1000):
        for info in chunk_data:
            info["timestamp_utc"] = info["timestamp_utc"][:-4]
        session.bulk_insert_mappings(StorePings, chunk_data)
        session.commit()


seed_store_timings()
