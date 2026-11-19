import json


class MatchAny:
    def __eq__(self, _: object) -> bool:
        return True


def parse_sse_events(text: str) -> list[dict]:
    """Parse SSE response text into a list of events with 'event' and 'data' keys."""
    events = []
    current: dict = {}
    for line in text.splitlines():
        if line.startswith("event:"):
            current["event"] = line[len("event:") :].strip()
        elif line.startswith("data:"):
            current["data"] = json.loads(line[len("data:") :].strip())
        elif line == "" and current:
            events.append(current)
            current = {}
    if current:
        events.append(current)
    return events


def add_household_member(api_client, admin_token, user) -> None:
    """KH: gives USER someone to inherit their recipes and lists, which deleting an account now needs (D78)."""
    from tests.utils import api_routes, factories

    group = api_client.get(api_routes.groups_self, headers=user.token).json()
    household = api_client.get(api_routes.households_self, headers=user.token).json()
    member = {
        "fullName": factories.random_string(),
        "username": factories.random_string(),
        "email": factories.random_email(),
        "password": "useruser",
        "group": group["name"],
        "household": household["name"],
        "admin": False,
    }
    assert api_client.post(api_routes.admin_users, json=member, headers=admin_token).status_code == 201
