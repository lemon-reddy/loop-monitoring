from . import read_csv
from monitor.model import StoreTimezones
from monitor.session import db_session as session


def seed_store_timings(filename="bq_results.csv"):
    for chunk_data in read_csv(filename=filename, window_size=1000):
        session.bulk_insert_mappings(StoreTimezones, chunk_data)
        session.commit()


seed_store_timings()
