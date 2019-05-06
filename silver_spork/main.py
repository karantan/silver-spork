"""Entry point."""

from kubernetes import client
from kubernetes import config
from kubernetes import utils
from kubernetes.stream import stream
from kubernetes.watch import Watch
from pprint import pprint
from silver_spork.const import Deployments
from silver_spork.const import KUBE_CONFIG
from silver_spork.const import Secrets
from silver_spork.const import Services
from silver_spork.const import Storage
from tinydb import Query
from tinydb import TinyDB

import click
import re
import structlog
import yaml

logger = structlog.get_logger(__name__)
db = TinyDB("db.json")


def add_label(key, value, k8s_yaml):
    """Add 'domain: `domain`' label to k8s object.

    Args:
        key (str): Label key.
        value (str): Label value.
        k8s_yaml (dict): Loaded Kubernetes object (e.g. deployment, service, ...)
    """
    k8s_yaml["metadata"]["labels"][key] = value
    return k8s_yaml


def create_deployment(deployment_file, domain):
    """Create a deployment on k8s cluster.

    The same thing if you would do:

    $ kubectl create -f <deployment_file>

    Args:

        deployment_file (str): File path to yaml deployment file.
        domain (str): Domain name used for namespace.
    """

    with open(deployment_file, "r") as f:
        yaml_file = yaml.safe_load(f)
        api_instance = client.AppsV1Api()
        resp = api_instance.create_namespaced_deployment(
            body=yaml_file, namespace=domain, pretty="true"
        )
    logger.info(f"Deployment {domain} done.")


def create_secret(secret_file, domain):
    """Create a secret on k8s cluster.

    The same thing if you would do:

    $ kubectl create -f <secret_file>

    Args:
        secret_file (str): File path to yaml secret file.
        domain (str): Domain name used for namespace.
    """

    with open(secret_file, "r") as f:
        yaml_file = yaml.safe_load(f)
        api_instance = client.CoreV1Api()
        resp = api_instance.create_namespaced_secret(
            body=yaml_file, namespace=domain, pretty="true"
        )
    logger.info(f"Secret {domain} configured.")


def create_service(service_file, domain):
    """Create a service on k8s cluster.

    The same thing if you would do:

    $ kubectl create -f <service_file>

    Args:
        service_file (str): File path to yaml service file.
        domain (str): Domain name used for namespace.
    """

    with open(service_file, "r") as f:
        yaml_file = yaml.safe_load(f)
        api_instance = client.CoreV1Api()
        resp = api_instance.create_namespaced_service(
            body=yaml_file, namespace=domain, pretty="true"
        )
    logger.info(f"Service {domain} configured.")


def create_storage(storage_file, domain):
    """Create a storage on k8s cluster.

    The same thing if you would do:

    $ kubectl create -f <storage_file>

    Args:
        storage_file (str): File path to yaml storage file.
        domain (str): Domain name used for namespace.
    """

    with open(storage_file, "r") as f:
        yaml_file = yaml.safe_load(f)
        api_instance = client.CoreV1Api()
        resp = api_instance.create_namespaced_persistent_volume_claim(
            body=yaml_file, namespace=domain, pretty="true"
        )
    logger.info(f"Storage {domain} configured.")


def create_namespace(domain):
    """Create namespace.

    Args:
        domain (str): Domain name used for creating namespace.
    """
    namespace_body = {
        "kind": "Namespace",
        "apiVersion": "v1",
        "metadata": {"name": domain, "labels": {"domain": domain}},
    }
    api_instance = client.CoreV1Api()
    api_instance.create_namespace(namespace_body)


def run_deploy(domain):
    """Deploy a WP blog on Kubernetes cluster.

    Args:
        domain (str): Domain name used for adding label.
    """

    create_namespace(domain)

    for secret in Secrets:
        create_secret(secret.value, domain)

    for deploy in Deployments:
        create_deployment(deploy.value, domain)

    for service in Services:
        create_service(service.value, domain)

    for storage in Storage:
        create_storage(storage.value, domain)

    blogs = db.table("blogs")
    blog_ip = None
    blogs.insert({"domain": domain, "ip": blog_ip, "deployed": False})

    v1 = client.CoreV1Api()
    logger.info("Waiting for Load Balancer's IP ...")
    watcher = Watch()
    resp = watcher.stream(
        v1.list_namespaced_service,
        namespace=domain,
        watch=True,
        label_selector="app=blog",
    )
    for service in resp:
        logger.info("Still waiting for Load Balancer to get an external IP ...")
        if (
            service["object"].status.load_balancer.ingress
            and service["object"].spec.type == "LoadBalancer"
        ):
            blog_ip = service["object"].status.load_balancer.ingress[0].ip
            watcher.stop()

    Blog = Query()
    blogs.update({"ip": blog_ip, "deployed": True}, Blog.domain == domain)

    logger.info(f"Successfully deployed blog {domain}.", ip=blog_ip)


def delete_deployment(namespace, label):
    """Delete a deployment on k8s cluster.

    The same thing if you would do:

    $ kubectl delete deploy -l <label> --namespace=<namespace>

    Args:
        namespace (str): Namespace of the deployment.
        label (str): Label for selecting deployments. Example: "app=blog".
    """

    k8s_beta = client.AppsV1Api()
    resp = k8s_beta.delete_collection_namespaced_deployment(
        namespace=namespace, label_selector=label, pretty="true"
    )
    logger.info(f"Deployment on '{namespace}' namespace with labels '{label}' deleted.")


def delete_secret(namespace, label):
    """Delete a secret on k8s cluster.

    The same thing if you would do:

    $ kubectl delete secret -l <label> --namespace=<namespace>

    Args:
        namespace (str): Namespace of the secret.
        label (str): Label for selecting secret. Example: "app=blog".
    """

    k8s_beta = client.CoreV1Api()
    resp = k8s_beta.delete_collection_namespaced_secret(
        namespace=namespace, label_selector=label, pretty="true"
    )
    logger.info(f"Secret on '{namespace}' namespace with labels '{label}' deleted.")


def delete_service(namespace, name):
    """Delete a service on k8s cluster.

    The same thing if you would do:

    $ kubectl delete service <name> --namespace=<namespace>

    Args:
        namespace (str): Namespace of the service.
        name (str): Name of the service.
    """

    k8s_beta = client.CoreV1Api()
    resp = k8s_beta.delete_namespaced_service(
        name=name, namespace=namespace, pretty="true"
    )
    logger.info(f"Service on '{namespace}' namespace with name '{name}' deleted.")


def delete_storage(namespace, label):
    """Delete a storage on k8s cluster.

    The same thing if you would do:

    $ kubectl delete pvc -l <label> --namespace=<namespace>

    Args:
        namespace (str): Namespace of the storage.
        label (str): Label for selecting storage. Example: "app=blog".
    """

    k8s_beta = client.CoreV1Api()
    resp = k8s_beta.delete_collection_namespaced_persistent_volume_claim(
        namespace=namespace, label_selector=label, pretty="true"
    )
    logger.info(
        f"PVC storage on '{namespace}' namespace with labels '{label}' deleted."
    )


def delete_namespace(domain):
    """Delete a namespace.

    Args:
        domain (str): Domain name used for removing a namespace.
    """
    api_instance = client.CoreV1Api()
    api_instance.delete_namespace(name=domain)

    logger.info(f"Namespace {domain} removed.")


def run_destroy(domain):
    """Remove WP blog from Kubernetes cluster."""

    delete_deployment(namespace=domain, label="app=blog")
    delete_secret(namespace=domain, label="app=blog")

    for item in Services:
        with open(item.value, "r") as f:
            ser = yaml.safe_load(f)
            delete_service(namespace=domain, name=ser["metadata"]["name"])

    delete_storage(namespace=domain, label="app=blog")
    delete_namespace(domain)

    blogs = db.table("blogs")
    Blog = Query()
    blogs.remove(Blog.domain == domain)

    logger.info(f"Successfully removed blog {domain}.")


@click.command()
@click.option(
    "--domain",
    prompt="Enter the domain of the blog you want to deploy. It must consist of lower case alphanumeric characters or '-', and must start and end with an alphanumeric character (e.g. 'my-name',  or '123-abc'",
)
def deploy(domain):
    """Deploy a WP blog on a Kubernetes cluster."""
    logger.info(f"Deploying {domain} WP blog on DigitalOcean Kubernetes cluster ...")
    run_deploy(domain)


@click.command()
@click.option(
    "--domain",
    prompt="Enter the domain of the blog you want to remove. It must consist of lower case alphanumeric characters or '-', and must start and end with an alphanumeric character (e.g. 'my-name',  or '123-abc'",
)
def destroy(domain):
    """Remove WP blog from Kubernetes cluster."""
    logger.info(f"Removing {domain} WP blog from Kubernetes cluster ...")
    run_destroy(domain)


@click.command()
def list_blogs():
    """Get list of all blogs deployed on the kubernetes cluster."""
    print("We have the following blogs deployed on the kubernetes cluster:")
    blogs = db.table("blogs")

    for blog in blogs.all():
        print(
            f"Domain {blog['domain']}, ip: {blog.get('ip')}, fully deployed: {blog.get('deployed')}"
        )


@click.group()
@click.option(
    "--config_file",
    type=click.Path(exists=True),
    default=KUBE_CONFIG,
    help="Path to kube-config yaml file.",
    show_default=True,
)
def cli(config_file):
    """Main entry point.

    Args:
        config_file (str): File path to the kube-config file.

    """
    try:
        config.load_kube_config(config_file=config_file)
    except Exception as e:
        logger.error(
            "Kubernetes configuration not set. `deploy` and `destroy` commands will not work"
        )


cli.add_command(deploy)
cli.add_command(destroy)
cli.add_command(list_blogs)

if __name__ == "__main__":
    cli()
