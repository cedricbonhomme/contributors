#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import pathlib
from collections import Counter
from python_graphql_client import GraphqlClient

root = pathlib.Path(__file__).parent.resolve()
client = GraphqlClient(endpoint="https://api.github.com/graphql")


TOKEN = os.environ.get("CONTRIBUTORS_TOKEN", "")


def replace_chunk(content, marker, chunk):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    chunk = "<!-- {} starts -->\n{}\n<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)


def make_query(after_cursor=None, owner="", name=""):
    query = """
query {
  repository(owner: "OWNER", name: "NAME") {
    defaultBranchRef {
      target {
        ... on Commit {
          history(after: AFTER) {
            pageInfo {
              hasNextPage
              endCursor
            }
            totalCount
            edges {
              node {
                ... on Commit {
                  committer {
                    user {
                      login
                      databaseId
                    }
                    avatarUrl(size: 100)
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
""".replace(
        "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )
    query = query.replace("OWNER", owner)
    query = query.replace("NAME", name)
    return query


def fetch_contributors(oauth_token, owner, name):
    has_next_page = True
    after_cursor = None

    limit = 0

    contributors_elem = {}
    contributors_cnt = Counter()
    while has_next_page:
        data = client.execute(
            query=make_query(after_cursor, owner, name),
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )

        for node in data["data"]["repository"]["defaultBranchRef"]["target"]["history"][
            "edges"
        ]:
            if None is not node["node"]["committer"]["user"]:
                if None is contributors_cnt.get(
                    node["node"]["committer"]["user"]["databaseId"]
                ):
                    contributors_elem[
                        node["node"]["committer"]["user"]["databaseId"]
                    ] = node["node"]["committer"]
                contributors_cnt[node["node"]["committer"]["user"]["databaseId"]] += 1

        has_next_page = data["data"]["repository"]["defaultBranchRef"]["target"][
            "history"
        ]["pageInfo"]["hasNextPage"]
        after_cursor = data["data"]["repository"]["defaultBranchRef"]["target"][
            "history"
        ]["pageInfo"]["endCursor"]
        limit += 1
        if limit >= 500:
            has_next_page = False

    return contributors_elem, contributors_cnt


if __name__ == "__main__":
    readme = root / "README.md"

    projects = [
        ("MISP", "MISP"),
        ("MISP", "PyMISP"),
        ("monarc-project", "MonarcAppFO"),
        ("cedricbonhomme", "stegano"),
        ("CIRCL", "AIL-framework"),
        ("CASES-LU", "Fit4Cybersecurity"),
        ("cve-search", "cve-search")
    ]
    rewritten = readme.open().read()
    for project in projects:
        contributors_elem, contributors_cnt = fetch_contributors(
            TOKEN, project[0], project[1]
        )
        commons = contributors_cnt.most_common(200)
        md = "\n".join(
            [
                '<a href="https://github.com/{0}"><img src="{1}" title="{2} commits" width="50px" /></a>'.format(
                    contributors_elem[contributor]["user"]["login"],
                    contributors_elem[contributor]["avatarUrl"],
                    count,
                )
                for contributor, count in commons
            ]
        )
        rewritten = replace_chunk(
            rewritten, "contributors-{}".format(project[1]), md
        )

    readme.open("w").write(rewritten)
