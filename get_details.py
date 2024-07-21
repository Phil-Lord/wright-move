import requests


def get_linley_and_simpson_listings() -> dict[str, str]:
    '''
    Get Linley and Simpson rental listings in Harrogate below £900pcm.

    :return dict[str, str]: A dictionary of listing display addresses to urls.
    '''

    # Create POST request for listings
    url = 'https://w73nr8xhev-dsn.algolia.net/1/indexes/prod_properties/query'
    params = {
        'x-algolia-agent': 'Algolia for JavaScript (4.24.0); Browser (lite)',
        'x-algolia-api-key': '6a218293b68c1af692910f073784b37d',
        'x-algolia-application-id': 'W73NR8XHEV'
    }
    data = {
        'query': '\"harrogate\"',
        'filters': '(department:residential) OR (department:auction) AND (search_type:lettings) OR (searchType:lettings) AND (price <= 900) AND (publish: true) AND (status:\"To Let\" OR status:\"Let Agreed\")',
        'page': 0,
        'hitsPerPage': 20
    }
    response = requests.post(url, params=params, json=data)

    listings = {}

    if response.status_code == 200:
        # Extract display address and url from response
        raw_listings = response.json()['hits']
        for i in range(0, len(raw_listings)):
            listing = raw_listings[i]
            listing_display_address = listing['display_address']
            listing_url = f'https://www.linleyandsimpson.co.uk/property-to-rent/{listing["slug"]}-{listing["objectID"]}'
            listings[listing_display_address] = listing_url
    else:
        print(f"Request failed with status code {response.status_code}")
        print(response.text)
    
    return listings
