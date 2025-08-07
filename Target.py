import requests
import html
import uuid
import datetime
import time
import random


from pathlib import Path
from glom import glom

from target_db import insert_product, insert_stock, insert_store, get_tcins_missing_metadata

HEADERS = {"User-Agent": "Mozilla/5.0"}
GLOBAL_KEY = "9f36aeafbe60771e321a7cc95a78140772ab3e96"
GLOBAL_ZIP = "98042"
GLOBAL_LIMIT = 5
REQUEST_DELAY = 1.0

def safe_get(url, params=None, headers=None, max_retries=3, delay=REQUEST_DELAY, backoff=10):
    for attempt in range(max_retries):
        res = requests.get(url, params=params, headers=headers)

        if res.status_code == 429:
            print("[!] Rate limit hit (429). Sleeping before retry...")
            time.sleep(backoff)
            continue

        try:
            res.raise_for_status()
            rand_sleep = delay + random.uniform(0, 0.5)
            print(f"Http req... sleeping for {rand_sleep}")
            time.sleep(rand_sleep)
            return res
        except requests.exceptions.RequestException as e:
            print(f"[!] Request failed: {e}. Retrying...")
            time.sleep(delay)
    raise Exception(f"Request to {url} failed after {max_retries} retries.")


def get_nearby_store_id_by_zip(limit = GLOBAL_LIMIT):
    url = "https://redsky.target.com/redsky_aggregations/v1/web/nearby_stores_v1"
    params = {
        "limit": limit, #how many stores to return
        "within": "100", #miles radius
        "place": GLOBAL_ZIP, #zip or city
        "key": GLOBAL_KEY,
        "channel": "WEB",
        "page": "/c/27p31"
    }

    res = safe_get(url, params=params, headers=HEADERS)    
    data = res.json()

    return glom(data, ("data.nearby_stores.stores", ["store_id"]), default=[])[:limit]

def get_nearby_store_id(tcin, limit = GLOBAL_LIMIT):
    stores_dict = {}
    url = "https://redsky.target.com/redsky_aggregations/v1/web/nearby_stores_v1"
    
    params = {
        "limit": limit, #how many stores to return
        "within": "100", #miles radius
        "place": GLOBAL_ZIP, #zip or city
        "key": GLOBAL_KEY,
        "channel": "WEB",
        "page": f"/p/A-{tcin}"
    }

    res = safe_get(url, params=params, headers=HEADERS)
    data = res.json()

    store_ids = glom(data, ("data.nearby_stores.stores", ["store_id"]), default = [])
    
    for store in data.get("data", {}).get("nearby_stores", {}).get("stores", []):
        store_id = store.get("store_id")
        store_name = store.get("location_name")
        store_address = store.get("mailing_address", {}).get("address_line1")

        if store_id and store_name and store_address:
            stores_dict[store_id] = {
                "store_name": store_name,
                "store_address": store_address
            }
        if not (store_id and store_name and store_address):
            print("[!] Incomplete store skipped:")
            print(f"store_id: {store_id}")
            print(f"store_name: {store_name}")
            print(f"store_address: {store_address}")

    for store_id, store_data in stores_dict.items():
       store_name = store_data["store_name"]
       store_address = store_data["store_address"]
       insert_store(store_id, store_name, store_address)


    return store_ids[:limit]

def get_product_metadata(tcin, store_id=None):
    url = "https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1"

    params = {
        "key": GLOBAL_KEY,
        "tcin": tcin,
        "channel": "WEB"
    }

    if store_id:
        params["pricing_store_id"] = store_id

    res = safe_get(url, params=params, headers=HEADERS)
    data = res.json()

    parsed_data = {
        "title": "data.product.item.product_description.title",
        "price": "data.product.price.current_retail",
        "buy_url": "data.product.item.enrichment.buy_url",
        "tcin_server": "data.product.tcin"
    }

    result = glom(data, parsed_data, default={})
    result["title"] = html.unescape(result.get("title", ""))
    result["tcin"] = result.get("tcin_server", tcin)
    result["price"] = result.get("price", None)

    # Insert into DB to cache
    print(f"\ninserting {result["title"]} with tcin of: {result["tcin"]}, and price of: {result["price"]}\n")
    insert_product(result["tcin"], result["title"], result["price"])

    return result


def get_target_data(tcin, limit = GLOBAL_LIMIT):

    nearby_store_list = get_nearby_store_id(tcin)

    url = "https://redsky.target.com/redsky_aggregations/v1/web/product_summary_with_fulfillment_v1"


    for store_id in nearby_store_list:
        
        params = {
            "key": GLOBAL_KEY,
            "tcins": tcin,
            "store_id": store_id,
            "channel": "WEB"
        }

        res = safe_get(url, params=params, headers=HEADERS)
        data = res.json()

        parsed_data = {
            "store_name": "data.product_summaries.0.fulfillment.store_options.0.store.location_name",
            "in_store_amount": "data.product_summaries.0.fulfillment.store_options.0.location_available_to_promise_quantity",
            "in_store_stock": "data.product_summaries.0.fulfillment.store_options.0.in_store_only.availability_status"
        }

        result = glom(data, parsed_data, default={})

        store_name = result.get("store_name")

        if not tcin or not store_name:
            continue
        
        meta = get_product_metadata(tcin, store_id)
        quantity = result.get("in_store_amount")
        availability = False
        last_available_at = None
        if result.get("in_store_stock") == "IN_STOCK":
            availability = True
            last_available_at = datetime.datetime.now().isoformat()
        
        #stock(id, tcin, store_id, quantity, availability, last_available_at, checked_at)
        insert_stock(
            tcin=tcin, 
            store_id=store_id,
            quantity = quantity, 
            availability = availability, 
            last_available_at = last_available_at,
            checked_at=datetime.datetime.now().isoformat()
        )
  
def get_tcin():

    tcins_output = set()

    #best seller top 10

    store_ids = get_nearby_store_id_by_zip()

    url = "https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v2"

    shared_params = {
        "key": GLOBAL_KEY,
        "channel": "WEB",
        "default_purchasability_filter": "true",
        "store_ids": store_ids,
        "pricing_store_id": store_ids[0],
        "visitor_id": uuid.uuid4().hex.upper(),
        "spellcheck": "true",
        "zip": GLOBAL_ZIP,
        "category": "27p31",
        "faceted_value": "569t0Zdq4mn",
        "page": "/c/collectible-trading-cards-hobby-collectibles-toys/pokemon/-/N-27p31Z569t0Zdq4mn"
    }
    
    best_selling_params = {**shared_params, "sort_by": "bestselling"}
    res = safe_get(url, params=best_selling_params, headers=HEADERS)
    data = res.json()

    products = data.get("data", {}).get("search", {}).get("products", [])
    tcins = [item["tcin"] for item in products[:10]]
    tcins_output.update(tcins)

    #newest 10

    url = "https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v2"
    newest_params = {**shared_params, "sort_by": "newest"}
    
    res = safe_get(url, params=newest_params, headers=HEADERS)
    data = res.json()

    products = data.get("data", {}).get("search", {}).get("products", [])
    tcins = [item["tcin"] for item in products[:10]]
    
    tcins_output.update(tcins)
    
    

    current_dir = Path(__file__).parent

    target_file = current_dir / "extraTCIN" / "manualTCIN.txt"

    with open(target_file, "r") as f:
        for line in f:
            tcin = line.strip()
            if tcin:
                tcins_output.add(tcin)

    for tcin in tcins_output:
        insert_product(tcin)

    return tcins_output

def backfill_missing_products():
    missing_tcins = get_tcins_missing_metadata()

    if missing_tcins:
        print(f"[i] Found {len(missing_tcins)} TCINs missing metadata")
        for tcin in missing_tcins:
            print(f"Fetching metadata for TCIN: {tcin}")
            try:
                get_product_metadata(tcin)
            except Exception as e:
                print(f"[!] Failed to fetch metadata for {tcin}: {e}")

def target_console():
    tcin_list = get_tcin()

    for tcin in tcin_list:
        get_target_data(tcin)

    backfill_missing_products()
