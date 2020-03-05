from csv import writer
from json import dumps
from requests import post

headers = {"Authorization": "token 08c66cd3119fa5ced6a6e21d0e07d879d7c33ddb"}


def run_query(query_):
    request = post(
        "https://api.github.com/graphql", json={"query": query_}, headers=headers
    )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(
            "Query failed to run by returning code of {}. {}".format(
                request.status_code, query_
            )
        )


query = """
query example{
  search(query:"stars:>100", type:REPOSITORY, first:50{AFTER}){
    pageInfo{
        hasNextPage
        endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        createdAt
        updatedAt
        pullRequests {
          totalCount
        }
        releases {
          totalCount
        }
        primaryLanguage {
          name
        }
        totalIssues: issues{
          totalCount
        }  
        totalClosesIssues: issues(states:CLOSED) {
          totalCount
        }      
      }
    }
  }
}
"""

finalQuery = query.replace("{AFTER}", "")
result = run_query(finalQuery)

totalPages = 1
currentEndCursor = result["data"]["search"]["pageInfo"]["endCursor"]
hasNextPage = result["data"]["search"]["pageInfo"]["hasNextPage"]
allResults = result["data"]["search"]["nodes"]

while hasNextPage and totalPages < 20:
    finalQuery = query.replace("{AFTER}", ', after: "%s"' % currentEndCursor)
    result = run_query(finalQuery)
    allResults += result["data"]["search"]["nodes"]

    totalPages += 1
    hasNextPage = result["data"]["search"]["pageInfo"]["hasNextPage"]
    currentEndCursor = result["data"]["search"]["pageInfo"]["endCursor"]

print(dumps(allResults, indent=4, sort_keys=True))

first_row = allResults[0].keys()

# Saving repositories' data to CSV file
with open("repos.csv", "w") as csv_file:
    csv = writer(csv_file)
    csv.writerow(first_row)
    for repo in allResults:
        csv.writerow(repo.values())
