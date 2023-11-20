# RETURNS False if event doesn't exist
# RETURNS the id of the event if it does.
def event_already_exists(supabase, event):  # TODO: could offload this to a trigger on the db
    # I wonder how bad using an ilike on a possibly large field like description is.
    data, count = supabase.table('events') \
        .select("*") \
        .ilike('event_name', event.event_name) \
        .ilike('description', event.description) \
        .execute()
    # TODO: How can we add in the within same time window check
    data = data[1]
    if data and len(data) > 0:  # Already in DB
        print("Already have this venue in the db", data[0])
        return data[0]["id"]  # I mean I didn't mean for this to return anything more than true or false... but not a bad feature?
    return False


def insert_dupe_event_db(supabase, event, preexisting_event_id, venue_db_id):
    data, count = supabase.table('dupes').insert({
        "event_name": event.event_name,
        "description": event.description,
        "event_datetime": f"{event.event_datetime}",
        "door_time": f"{event.door_time}",
        "price": event.price,
        "url": event.url,
        "image_url": event.image_url,
        "source_url": event.source_url,
        "venue": venue_db_id,
        "event_id": preexisting_event_id,
    }).execute()
    return data[1][0]


def insert_event_db(supabase, event, venue_id, calendar_event_id):
    print(event)
    print(venue_id)
    data, count = supabase.table('events').insert({
        "event_name": event.event_name,
        "description": event.description,
        "event_datetime": f"{event.event_datetime}",
        "door_time": f"{event.door_time}",
        "price": event.price,
        "url": event.url,
        "image_url": event.image_url,
        "source_url": event.source_url,
        "googleCalendarEventId": calendar_event_id,
        "venue": venue_id
    }).execute()
    print('inserted data', data[1])
    return data[1][0]


def get_or_insert_venue(supabase, venue_info):
    data, count = supabase.table('venues').select("id", "street_address").eq('street_address', venue_info.street_address).execute()
    data = data[1]
    if data and len(data) > 0:  # Already in DB
        print("Already have this venue in the db", data[0])
        return data[0]["id"]
    else:  # Add it
        print("Adding venue to the db", venue_info)
        res = supabase.table('venues').insert({
            "name": venue_info.venue_name,
            "street_address": venue_info.street_address,
            "state": venue_info.state,
            "postal_code": venue_info.postal_code,
        }).execute()
        data = res.data
        return data[0]['id']
