from datetime import datetime

FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def stamp():
    return datetime.utcnow().strftime(FORMAT)


def age_days(iso):
    then = datetime.strptime(iso, FORMAT)
    return (datetime.utcnow() - then).days
