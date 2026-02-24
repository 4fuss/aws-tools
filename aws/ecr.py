import boto3
import typer
from rich import print
import json

def main(profile, region, registry_id):
    session = boto3.Session(
        profile_name=profile,
        region_name=region
    )
    ecr = session.client("ecr")
    start_token = "start"
    next_token = start_token
    repos = []
    while next_token:
        args = {
                'registryId': registry_id,
                }
        if next_token != start_token:
            args.update({
                'nextToken': next_token
                })
        res = ecr.describe_repositories(**args)
        repos += res.get('repositories')
        next_token = res.get('nextToken')
    make_repo_def(session, repos)
    make_import_tf(repos)

sanitize_name = lambda n: n.replace('-','_').replace('/','_')

def add_immutable(mutability):
    if mutability == "IMMUTABLE":
        return f"\n\timage_tag_mutability = \"{mutability}\""
    return ""

def add_tags(session, arn):
    resp = session.client("ecr").list_tags_for_resource(resourceArn=arn)
    _tags = resp.get('tags')
    tags = {d["Key"]: d["Value"] for d in _tags}
    if tags:
        print(tags)
        return f"\n\ttags = {json.dumps(tags)}"
    else:
        print(".")
        return ""

def make_repo_def(session, repos):
    with open("repo_def.txt", "w") as f:
        for r in repos:
            arn = r.get('repositoryArn')
            repo_name = r.get('repositoryName')
            if 'docker-io' in repo_name:
                continue
            mutability = r.get('imageTagMutability')
            entry = f"""{sanitize_name(repo_name)} = {{
\tname = "{repo_name}"{add_immutable(mutability)}{add_tags(session, arn)}
}}
"""
            f.write(entry)

def make_import_tf(repos):
    with open("imported.tf", "w") as f:
        for r in repos:
            repo_name = r.get('repositoryName')
            entry = f"""import {{
\tto = aws_ecr_repository.this["{sanitize_name(repo_name)}"]
\tid = "{repo_name}"
}}
"""
            f.write(entry)
