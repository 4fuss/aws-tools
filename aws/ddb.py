import typer
import boto3
from rich import print

app = typer.Typer()

def _parse_attributes(attributes):
    attrs = {}
    for attr in attributes:
        name = attr.get('AttributeName')
        attr_type = attr.get('AttributeType')
        attrs[name] = attr_type
    return attrs

def _parse_keys(keys):
    _keys = {}
    for k in keys:
        key = k.get('AttributeName')
        key_type = k.get('KeyType')
        if key_type == "HASH":
            _keys["hash_key"] = key
        elif key_type == "RANGE":
            _keys["range_key"] = key
        else:
            raise Exception(f"Uknown key type {key_type}")
    return _keys

def _parse_index(indexes):
    ixs = []
    for ix in indexes:
        ix_name = ix['IndexName']
        keys = _parse_keys(ix['KeySchema'])
        projection_type = ix['Projection']['ProjectionType']
        keys.update({
            'name': ix_name,
            'projection_type': projection_type
        })
        ixs.append(keys)
    return ixs

@app.command("ddb-list")
def ddb_list():
    session = boto3.Session()
    dynamodb = session.client('dynamodb')
    resp = dynamodb.list_tables()
    tables = resp.get('TableNames')
    entry = {}

    for t in tables:
        res = dynamodb.describe_table(TableName=t)
        table = res.get('Table')
        attrs = _parse_attributes(table.get('AttributeDefinitions'))
        table_name = table.get('TableName')
        key_schema = _parse_keys(table.get('KeySchema'))
        indexes = table.get('GlobalSecondaryIndexes')
        global_secondary_indexes = _parse_index(indexes) if indexes is not None else None
        table_arn = table.get('TableArn')
        tags = dynamodb.list_tags_of_resource(ResourceArn=table_arn)
        entry[table_name] = {
            "name": table_name,
            "attributes": attrs
        }
        entry[table_name].update(key_schema)
        if global_secondary_indexes is not None:
            entry[table_name].update({
                "global_secondary_index": global_secondary_indexes
            })
    print(entry)

