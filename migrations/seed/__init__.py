import csv


def read_csv(filename, window_size=100):
    curr_store = []
    with open(filename, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            curr_store.append(dict(row))
            if (idx + 1) % window_size == 0:
                yield curr_store
                curr_store = []
        yield curr_store
