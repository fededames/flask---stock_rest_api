import datetime
import os
import itertools
import click
from flask import Flask, request, jsonify
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    db_url = os.environ.get("DATABASE_URL")

    if db_url is None:
        db_path = os.path.join(app.instance_path, "db.sqlite3")
        db_url = f"sqlite:///{db_path}"
        os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    db.init_app(app)
    id_iter = itertools.count(start=1)
    app.cli.add_command(init_db_command)

    @app.route("/", methods=["GET"])
    def home():
        return "hello", 200

    @app.route("/trades", methods=["POST"])
    def trades():
        content = request.get_json()
        content["id"] = next(id_iter)
        formatted_content = {**content}
        formatted_content["timestamp"] = datetime.datetime.fromtimestamp(content["timestamp"]/1000.0)
        db.session.add(Trade(**formatted_content))
        db.session.commit()
        return content, 201

    @app.route("/trades", methods=["GET"])
    def get_trades():
        args = request.args
        if args:
            trades = Trade.query.filter_by(**args)
        else:
            trades = Trade.query.all()

        result = [serialize(trade) for trade in trades ]
        return  jsonify(result), 200

    @app.route("/trades/<user_id>")
    def get_specific_trade(user_id):
        id = int(user_id)
        if Trade.query.get(id):
            return serialize(Trade.query.get(id)), 200
        else:
            return "", 404

    return app



def init_db():
    db.drop_all()
    db.create_all()
    
from app.models import Trade


@click.command("init-db")
@with_appcontext
def init_db_command():
    init_db()
    click.echo("Initialized the database.")

app = create_app()


def serialize(trade):
    return {
        "id": trade.id,
        "price": trade.price,
        "shares": trade.shares,
        "symbol": trade.symbol,
        "timestamp": int(trade.timestamp.timestamp()*1000),
        "type": trade.type,
        "user_id": trade.user_id
    }
