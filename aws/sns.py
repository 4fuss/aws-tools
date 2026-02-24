import typer
import boto3

app = typer.Typer()
FIRST_TOKEN = 'first'

@app.command()
def sns_list():
    session = boto3.Session()
    sns = session.client('sns')
    next_token = FIRST_TOKEN
    kw = {}
    while next_token:
        if next_token != FIRST_TOKEN:
            kw = {"NextToken": next_token}
        resp = sns.list_topics(**kw)
        topics = resp['Topics']
        next_token = resp.get('NextToken')
        for topic in topics:
            print(topic['TopicArn'])
