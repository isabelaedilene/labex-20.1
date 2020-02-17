import requests
import json

headers = {"Authorization": "key"}


def run_query(query): 
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
        
query = """
query example {
  search(query:"stars:>100",
    type:REPOSITORY, first:5){
    nodes {
      ... on Repository {
        nameWithOwner
        diskUsage
      }
    }
  }
}
"""

result = run_query(query) 
print(json.dumps(result, indent=4, sort_keys=True))

# nameWithOwner = result["data"]["search"]["nodes"]  
# print("nameWithOwner - {}".format(nameWithOwner))