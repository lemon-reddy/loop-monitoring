# Loop - Restaurant Monitoring System
Backend service to generate report of uptime and downtimes for all restaurants.

## Steps to run
- Install requirements.txt
- Run database migrations and seeder commands to populate database.
- Start app using uvicorn
```
pip install requirements.txt
alembic upgrade head
# Download csv files and store them in a path
python -m migrations.seed.store_pings
python -m migrations.seed.store_timings
python -m migrations.seed.store_timezones
uvicorn monitor:app     # Runs on port 8000
```

https://github.com/lemon-reddy/loop-monitoring/assets/75769543/ddb9a8c8-c7e2-4367-984c-d98939cf873b



### Tech Stack
**Python**: Python3.11.6
**Backend Framework**: FastAPI
**Databases**: MySQL, Redis
**Other libraries**: SQLAlchemy, uvicorn, pydantic, alembic, python-dotenv

## Logic used to compute uptimes and downtimes
**Time taken**~ 13 seconds
- Get all store_ids along with timezones and cache them.
- Query database for store pings in chunks(chunk_size = 500 store_ids) and convert those pings to local times using zoneinfo.
- Query database for open and close timings to calculate working hours.
- Finally aggregate results from chunk processing and store them in server filesystem with generated report_id(Should be migrated to external object stores in the future)

### Algorithm
- Validate pings by checking whether it lies in between that days opening and closing times. Ignore ping if validation fails.

#### Last hour
1. Loop through descending order of ping timestamps that fall within an hour and add the time elapsed to the uptime and downtimes.
2. Check the last timestamp before 1 hour from current time and update the remaining duration with that status.
3. uptime and downtimes for the last hour are obtained through this method.

#### Last day and Last Week
1. Count all the active and inactive timestamps in the past day and past week.
2. Calculate the working hours of the restaurant in the past day and past week.
3. Get uptime percentage from counts and multiply with the working hours for the past day and week.

## Further improvements
1. Task queue like celery or rq can be used to run the reports on a different machines.
2. asyncio integration to improve times.
3. Time profiling to identify the bottlenecks.
