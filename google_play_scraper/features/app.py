import json
from typing import Any, Dict

from google_play_scraper.constants.element import ElementSpecs
from google_play_scraper.constants.google_play import PageType
from google_play_scraper.constants.regex import Regex
from google_play_scraper.constants.request import Formats
from google_play_scraper.exceptions import NotFoundError
from google_play_scraper.utils.request import get


def app(app_id: str, lang: str = "en", country: str = "us") -> Dict[str, Any]:
    url = Formats.Detail.build(app_id=app_id, lang=lang, country=country)

    try:
        dom = get(url)
    except NotFoundError:
        url = Formats.Detail.fallback_build(app_id=app_id, lang=lang)
        dom = get(url)
    return parse_dom(dom=dom, app_id=app_id, url=url)


def parse_dom(dom: str, app_id: str, url: str) -> Dict[str, Any]:
    matches = Regex.SCRIPT.findall(dom)

    dataset = {}

    for match in matches:
        key_match = Regex.KEY.findall(match)
        value_match = Regex.VALUE.findall(match)

        if key_match and value_match:
            key = key_match[0]
            value = json.loads(value_match[0])

            dataset[key] = value

    result = {}
    
    for k, spec in ElementSpecs.Detail.items():
        content = spec.extract_content(dataset)
        if content is None:
            result[k] = spec.fallback_value
        else:
            result[k] = content

    try:
        for collection in ElementSpecs.DetailHelper["appCollections"].extract_content(
            dataset
        ):
            if result["developer"] in collection["title"]:
                result["moreByDeveloper"] = collection["appIds"]
            else:
                result["similarApps"] = collection["appIds"]
    except:
        pass

    try:
        for page in ElementSpecs.DetailHelper["appCollectionPages"].extract_content(
            dataset
        ):
            if result["developer"] in page["title"]:
                result["moreByDeveloperPage"] = {
                    "token": page["url"][35:]
                    if page["url"].startswith("/store/apps/collection/cluster")
                    else page["url"][19:]
                    if page["url"].startswith("/store/apps/dev")
                    else page["url"],
                    "type": PageType.COLLECTION
                    if page["url"].startswith("/store/apps/collection/cluster")
                    else PageType.DEVELOPER
                    if page["url"].startswith("/store/apps/dev")
                    else None,
                }
            else:
                result["similarAppsPage"] = {
                    "token": page["url"][35:],
                    "type": PageType.COLLECTION,
                }
    except:
        pass

    result["appId"] = app_id
    result["url"] = url

    return result
