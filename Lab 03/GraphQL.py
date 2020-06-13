from csv import writer
from json import dumps
from requests import post
import time

headers = {"Authorization": "token d639250f0483078d0045f9536419bb33f05ff100"}

repositoriesQuery = """
query repositoriesQuery {
  search(type: REPOSITORY, first: 100, query: "stars:>100 created:>=2016-01-01 language:python"{AFTER}) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        id
        nameWithOwner
        url
        stargazers {
          totalCount
        }
        issues {
          totalCount
        }
      }
    }
  }
}
"""

issuesQuery = """
query example {
  repository(owner: "{OWNER}", name: "{NAME}"){
    issues(first: 100, orderBy:{field: CREATED_AT, direction: ASC}{AFTER}){
      pageInfo{
        hasNextPage
        endCursor
      }
      nodes {
        id
        title
        createdAt
        closedAt
        closed
      }
    }    
  }
}
"""

def runQuery(query):
    request = post(
        'https://api.github.com/graphql', json={'query': query}, headers=headers
    )
    while (request.status_code == 502):
        time.sleep(2)
        request = post(
            'https://api.github.com/graphql', json={'query': query}, headers=headers
        )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query falhou! Codigo de retorno: {}. {}".format(request.status_code, query))

def getAllRepositories(query):
  finalQuery = query.replace("{AFTER}", "")
  result = runQuery(finalQuery)

  totalPages = 1
  hasNextPage = result["data"]["search"]["pageInfo"]["hasNextPage"]
  currentEndCursor = result["data"]["search"]["pageInfo"]["endCursor"]

  allResults = result["data"]["search"]["nodes"]

  while hasNextPage and totalPages <= 10:
    finalQuery = query.replace("{AFTER}", f', after: "{currentEndCursor}"')
    result = runQuery(finalQuery)

    totalPages += 1
    hasNextPage = result["data"]["search"]["pageInfo"]["hasNextPage"]
    currentEndCursor = result["data"]["search"]["pageInfo"]["endCursor"]
    
    allResults += result["data"]["search"]["nodes"]

  writeCSV("repositories.csv", allResults)

def getAllIssues(query):
  with open("repositories.csv", "r", encoding="utf-8") as f:
    lines = f.read()
    for line in lines.splitlines():
      line = line.split(",")

      nameWithOwner = line[1].split("/")
      owner = nameWithOwner[0]
      name = nameWithOwner[1]

      idRepository = line[0]

      allResults = getRepositoryIssues(owner, name, query)

      for result in allResults:
        result["idRepository"] = idRepository
        result["owner"] = owner
        result["name"] = name

      writeCSV("issues.csv", allResults)

def getRepositoryIssues(owner, name, query):
  finalQuery = query.replace("{OWNER}", owner).replace("{NAME}", name).replace("{AFTER}", "")
  result = runQuery(finalQuery)

  totalPages = 1
  currentEndCursor = result["data"]["repository"]["issues"]["pageInfo"]["endCursor"]
  hasNextPage = result["data"]["repository"]["issues"]["pageInfo"]["hasNextPage"]

  allResults = result["data"]["repository"]["issues"]["nodes"]

  while hasNextPage and totalPages <= 10:
    finalQuery = query.replace("{OWNER}", owner).replace("{NAME}", name).replace("{AFTER}", f', after: "{currentEndCursor}"')
    result = runQuery(finalQuery)

    totalPages += 1
    currentEndCursor = result["data"]["repository"]["issues"]["pageInfo"]["endCursor"]
    hasNextPage = result["data"]["repository"]["issues"]["pageInfo"]["hasNextPage"]

    allResults += result["data"]["repository"]["issues"]["nodes"]

  return allResults 

def writeCSV(file, allResults):
  with open(file, "a", newline = '', encoding="utf-8") as csv_file:
      csv = writer(csv_file)
      for result in allResults:
          csv.writerow(result.values())

def main():
  # getAllRepositories(repositoriesQuery)
  getAllIssues(issuesQuery)

main()
