import typer
from aws.ddb import app as ddb_app
from aws.sns import app as sns_app

app = typer.Typer()
app.add_typer(ddb_app) 
app.add_typer(sns_app)


if __name__ == "__main__":
    app()
