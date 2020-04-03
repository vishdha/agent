import json
import os
import shutil
import click

from agent.server import Server
from agent.proxy import Proxy
from agent.haproxy import HAProxy


@click.group()
def cli():
    pass


@cli.group()
def setup():
    pass


@cli.command()
def update():
    Server().update_agent_cli()


@setup.command()
@click.option("--name", required=True)
@click.option("--user", default="frappe")
@click.option("--workers", required=True, type=int)
def config(name, user, workers):
    config = {
        "benches_directory": f"/home/{user}/benches",
        "name": name,
        "tls_directory": f"/home/{user}/agent/tls",
        "nginx_directory": f"/home/{user}/agent/nginx",
        "redis_port": 25025,
        "user": user,
        "workers": workers,
        "web_port": 25052,
    }
    json.dump(config, open("config.json", "w"), sort_keys=True, indent=4)


@setup.command()
@click.option("--password", prompt=True, hide_input=True)
def authentication(password):
    Server().setup_authentication(password)


@setup.command()
def supervisor():
    Server().setup_supervisor()


@setup.command()
def nginx():
    Server().setup_nginx()


@setup.command()
@click.option("--domain")
def proxy(domain=None):
    proxy = Proxy()
    if domain:
        config = proxy.config
        config["domain"] = domain
        proxy.setconfig(config)
    proxy.setup_proxy()

@setup.command()
def database():
    from agent.job import agent_database as database
    from agent.job import JobModel, StepModel

    database.create_tables([JobModel, StepModel])


@cli.group()
def run():
    pass


@run.command()
def web():
    executable = shutil.which("gunicorn")
    port = Server().config["web_port"]
    arguments = [
        executable,
        "--bind",
        f"127.0.0.1:{port}",
        "--reload",
        "--preload",
        "agent.web:application",
    ]
    os.execv(executable, arguments)


@run.command()
def worker():
    executable = shutil.which("rq")
    port = Server().config["redis_port"]
    arguments = [
        executable,
        "worker",
        "--url",
        f"redis://127.0.0.1:{port}",
    ]
    os.execv(executable, arguments)
