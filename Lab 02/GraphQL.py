import requests
import time
import json
import git
from csv import writer
from radon import raw
from subprocess import Popen, PIPE
import os
from json import dumps
import shutil

headers = {"Authorization": "token d390c9e7ad2eb8bf54635d02c79d3f14e01334f6"}

def run_query(query):
    request = requests.post(
        'https://api.github.com/graphql', json={'query': query}, headers=headers
    )
    while (request.status_code == 502):
        time.sleep(2)
        request = requests.post(
            'https://api.github.com/graphql', json={'query': query}, headers=headers
        )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query falhou! Codigo de retorno: {}. {}".format(request.status_code, query))

query = """
query MyQuery{
  search(type: REPOSITORY, query: "{REPLACE} language:python", first: 5{AFTER}) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        ... on Repository {
          name
          url
          forkCount
          primaryLanguage{
            name
          }
          stargazers {
            totalCount
          }
          watchers {
            totalCount
          }
          releases {
            totalCount
          }
          createdAt          
        }
      }
    }
  }
}
"""

def createFiles (nameFile, results):
  for result in results:
    name = result["node"]["name"]
    url = result["node"]["url"]
    print(f"Clonando repositório {url} ...")
    if os.path.exists(name):
      print("O diretório já existe.")
    else:
      print("O diretório z não existe.")
      git.Git().clone(url)

    print(f"Calculando LOC de {name} ...")
    out, err = Popen(
      ["radon", "raw", name, "-O", f"LOC_{name}.txt"], stdout=PIPE, stderr=PIPE
    ).communicate()
    print(out)

    with open(f"LOC_{name}.txt", "r") as file:
      loc = 0

      allLines = file.read()
      for line in allLines.splitlines():
        if " LOC:" in line:
          loc += int(line.split(": ")[1])
          print(loc)
      print(f"{name} - {loc}")

    with open(f"{nameFile}.csv", "w") as csv_file:
      csv = writer(csv_file)    
      csv.writerow([result["node"].values(), f"Loc: {loc}"])

    print("Excluindo diretórios e arquivos ...")
    dirPath =  f'{name}/'
    shutil.rmtree(dirPath, ignore_errors=True)
    os.remove(f"LOC_{name}.txt")


#### Parte 1 - Repositórios Guido

queryGuido = query.replace("{REPLACE}", "user:gvanrossum").replace("{AFTER}", "")
resultsGuido = run_query(queryGuido)
# print(dumps(resultsGuido, indent=4, sort_keys=True))
createFiles (nameFile = "reposGuido",results = resultsGuido["data"]["search"]["edges"])

#### Parte 2 - Repositórios Python

queryPython = query.replace("{REPLACE}", "").replace("{AFTER}", "")
resultsPython = run_query(queryPython)
# print(dumps(resultsPython, indent=4, sort_keys=True))

totalPages = 1
currentEndCursor = resultsPython["data"]["search"]["pageInfo"]["endCursor"]
hasNextPage = resultsPython["data"]["search"]["pageInfo"]["hasNextPage"]
allResultsPython = resultsPython["data"]["search"]["edges"]

while hasNextPage and totalPages < 2:
    queryPython = queryPython.replace("{AFTER}", ', after: "%s"' % currentEndCursor)
    resultsPython = run_query(queryPython)

    for result in resultsPython["data"]["search"]["edges"]:
      allResultsPython.append(result)

    totalPages += 1
    hasNextPage = resultsPython["data"]["search"]["pageInfo"]["hasNextPage"]
    currentEndCursor = resultsPython["data"]["search"]["pageInfo"]["endCursor"]

createFiles("reposPython", allResultsPython)


print(dumps(allResultsPython, indent=4, sort_keys=True))
