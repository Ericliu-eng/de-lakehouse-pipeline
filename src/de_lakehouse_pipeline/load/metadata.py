from datetime import date


def record_load(source: str, load_date: str, version: str, record_count: int):

    metadata_payload = {
        "source": source,
        "load_date": load_date,
        "version": version,
        "record_count": record_count,
        "recorded_at": date.today().isoformat()
        
    }

    print("Metadata to record:", metadata_payload)

    return metadata_payload