import requests
import html

from glom import glom

def get_nearby_store_id(tcin, zip_code, limit):
    url = "https://redsky.target.com/redsky_aggregations/v1/web/nearby_stores_v1"
    
    params = {
        "limit": limit, #how many stores to return
        "within": "100", #miles radius
        "place": zip_code, #zip or city
        "key": "9f36aeafbe60771e321a7cc95a78140772ab3e96",
        "channel": "WEB",
        "page": f"/p/A-{tcin}"
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, params=params, headers=headers)
    res.raise_for_status()
    data = res.json()

    store_ids = glom(data, ("data.nearby_stores.stores", ["store_id"]), default = [])

    return store_ids[:limit]


def check_target_product_summary(tcin, zip_code, limit=20):
    
    compiled_store_info = {}
    #the list should be done with TCIN number

    nearby_store_list = get_nearby_store_id(tcin, zip_code, limit)

    url = "https://redsky.target.com/redsky_aggregations/v1/web/product_summary_with_fulfillment_v1"


    for stores in nearby_store_list:
        
        params = {
            "key": "9f36aeafbe60771e321a7cc95a78140772ab3e96",
            "tcins": tcin,
            #"zip": zip_code,
            "store_id": stores,
            "channel": "WEB"
        }

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        res = requests.get(url, params=params, headers=headers)
        res.raise_for_status()
        data = res.json()
        print(data)

        #print(data)

        parsed_data = {
            "title": "data.product_summaries.0.item.product_description.title",
            "store_name": "data.product_summaries.0.fulfillment.store_options.0.store.location_name",
            "in_store_stock": "data.product_summaries.0.fulfillment.store_options.0.in_store_only.availability_status",
            "in_store_amount": "data.product_summaries.0.fulfillment.store_options.0.location_available_to_promise_quantity",
            "tcin_server": "data.product_summaries.0.tcin"
        }

        result = glom(data, parsed_data, default={})
        tcin = result.get("tcin_server")
        store_name = result.get("store_name")
        product_title = html.unescape(result.get("title"))
        if not tcin or not store_name:
            continue
        
        if result.get("in_store_stock") == "IN_STOCK":
            #tcin and store dictionary creation
            if tcin not in compiled_store_info:
                compiled_store_info[tcin] = {
                    "title": product_title,
                    "stores": {}
                }
            #updating store info under that tcin
            compiled_store_info[tcin]["stores"][store_name] = {
                "in_store_stock": result.get("in_store_stock"),
                "in_store_amount": result.get("in_store_amount")
            }
        
    if not compiled_store_info:
        print(f"{product_title} is out of stock at the nearest {limit} stores")
    else:
        print(f"Target Store info:\n{compiled_store_info}")
        
    

# Test run
check_target_product_summary("94724987", "98042")
