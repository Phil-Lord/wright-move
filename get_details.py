import requests

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

if response.status_code == 200:
    hits = response.json()['hits']
    for i in range(0, len(hits)):
        print(hits[i]['display_address'])
else:
    print(f"Request failed with status code {response.status_code}")
    print(response.text)
