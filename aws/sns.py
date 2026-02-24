import typer
import boto3
from rich import print

app = typer.Typer()

def parse_topic_attrs(attrs):
    key_map = {
        'TopicArn': 'topic_arn',
        'DisplayName': 'display_name',
        'TracingConfig': 'tracing_config',
        'ContentBasedDeduplication': 'content_based_deduplication',
        'FifoTopic': 'fifo_topic'
    }
    attr_map = lambda d: {key_map[k]: d[k] for k in key_map if k in d}
    new_attrs = attr_map(attrs)
    if 'display_name' in new_attrs and len(new_attrs['display_name']) == 0:
        del new_attrs['display_name']
    return new_attrs

def gen_sns_list(session, with_attrs=True):
    sns = session.client('sns')
    next_token = None
    while True:
        kw = {"NextToken": next_token} if next_token else {}
        resp = sns.list_topics(**kw)
        for topic in resp['Topics']:
            arn = topic['TopicArn']
            if with_attrs:
                attrs = sns.get_topic_attributes(TopicArn = arn)
                tags = sns.list_tags_for_resource(ResourceArn = arn)['Tags']
                new_attrs = parse_topic_attrs(attrs['Attributes'])
                if len(tags) > 0:
                    _tags = {t['Key']: t['Value'] for t in tags}
                    new_attrs['tags'] = _tags
                yield new_attrs
            else:
                yield parse_topic_attrs(topic)
        next_token = resp.get('NextToken')
        if not next_token:
            break

@app.command()
def sns_list():
    session = boto3.Session()
    for topic in gen_sns_list(session):
        print(topic)

def get_sns_key(topic):
    arn = topic.pop('topic_arn')
    name = arn.split(":")[-1]
    key = name.replace("-", "_").replace(".", "_")
    return (key, arn)

def get_tf_block(topic):
    key, arn = get_sns_key(topic)
    name = arn.split(":")[-1]
    body = f"name = \"{name}\""
    bools = ['true', 'false']
    quote = lambda e: e if e in bools else f"\"{e}\""
    for k in topic:
        body += f"\n{k} = {quote(topic[k])}"
    return f"""{key} = {{
{body}
}}"""

def get_tf_import(topic):
    key, arn = get_sns_key(topic)
    return f"""import {{
  to = aws_sns_topic.this["{key}"]
  id = "{arn}"
}}"""

@app.command('sns-tf-block')
def sns_tf_block():
    session = boto3.Session()
    for topic in gen_sns_list(session):
        block = get_tf_block(topic)
        print(block)

@app.command('sns-tf-import')
def sns_import_block():
    session = boto3.Session()
    for topic in gen_sns_list(session, with_attrs=False):
        block = get_tf_import(topic)
        print(block)
