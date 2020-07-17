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
          history(after: null) {
            pageInfo {
              hasNextPage
              endCursor
            }
            totalCount
            edges {
              node {
                ... on Commit {
                  committer {
                    name
                    email
                    user {
                      name
                    }
                    date
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
                if not contributors_elem.get(node["node"]["committer"]["name"], False):
                    contributors_elem[node["node"]["committer"]["email"]] = node["node"]["committer"]
                    contributors_cnt[node["node"]["committer"]["email"]] += 1

        has_next_page = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]["pageInfo"][
            "hasNextPage"
        ]
        after_cursor = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]["pageInfo"][
            "endCursor"
        ]
        limit += 1
        if limit >= 450:
            has_next_page = False

    return contributors_elem, contributors_cnt


if __name__ == "__main__":
    readme = root / "README.md"

    contributors_elem, contributors_cnt = fetch_contributors(TOKEN, "MISP", "MISP")
    commons = contributors_cnt.most_common(200)
    md = "\n".join(
        [
            '<a href="https://github.com/{0}"><img src="{1}" title="{2}" width="100px" /></a>'.format(contributors_elem[contributor]["name"], contributors_elem[contributor]["avatarUrl"], count)
            for contributor, count in commons
        ]
    )
    readme_contents = readme.open().read()
    rewritten = replace_chunk(readme_contents, "contributors-MISP", md)
    
    
    contributors_elem, contributors_cnt = fetch_contributors(TOKEN, "MISP", "PyMISP")
    commons = contributors_cnt.most_common(200)
    md = "\n".join(
        [
            '<a href="https://github.com/{0}"><img src="{1}" title="{2}" width="100px" /></a>'.format(contributors_elem[contributor]["name"], contributors_elem[contributor]["avatarUrl"], count)
            for contributor, count in commons
        ]
    )
    readme_contents = readme.open().read()
    rewritten = replace_chunk(rewritten, "contributors-PyMISP", md)
    
    
    contributors_elem, contributors_cnt = fetch_contributors(TOKEN, "monarc-project", "MonarcAppFO")
    commons = contributors_cnt.most_common(200)
    md = "\n".join(
        [
            '<a href="https://github.com/{0}"><img src="{1}" title="{2}" width="100px" /></a>'.format(contributors_elem[contributor]["name"], contributors_elem[contributor]["avatarUrl"], count)
            for contributor, count in commons
        ]
    )
    readme_contents = readme.open().read()
    rewritten = replace_chunk(rewritten, "contributors-MONARC", md)


    contributors_elem, contributors_cnt = fetch_contributors(TOKEN, "cedricbonhomme", "stegano")
    commons = contributors_cnt.most_common(200)
    md = "\n".join(
        [
            '<a href="https://github.com/{0}"><img src="{1}" title="{2}" width="100px" /></a>'.format(contributors_elem[contributor]["name"], contributors_elem[contributor]["avatarUrl"], count)
            for contributor, count in commons
        ]
    )
    readme_contents = readme.open().read()
    rewritten = replace_chunk(rewritten, "contributors-stegano", md)
    
    
    contributors_elem, contributors_cnt = fetch_contributors(TOKEN, "CIRCL", "AIL-framework")
    commons = contributors_cnt.most_common(200)
    md = "\n".join(
        [
            '<a href="https://github.com/{0}"><img src="{1}" title="{2}" width="100px" /></a>'.format(contributors_elem[contributor]["name"], contributors_elem[contributor]["avatarUrl"], count)
            for contributor, count in commons
        ]
    )
    readme_contents = readme.open().read()
    rewritten = replace_chunk(rewritten, "contributors-AIL-framework", md)


    readme.open("w").write(rewritten)
