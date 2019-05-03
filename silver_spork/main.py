"""Entry point."""

from kubernetes import client
from kubernetes import config
from kubernetes import utils
from kubernetes.stream import stream
from pprint import pprint
from silver_spork.const import Deployments
from silver_spork.const import KUBE_CONFIG
from silver_spork.const import Secrets
from silver_spork.const import Services
from silver_spork.const import Storage
from kubernetes.watch import Watch

import click
import structlog
import yaml

logger = structlog.get_logger(__name__)


def create_deployment(deployment_file):
    """Create a deployment on k8s cluster.

    The same thing if you would do:

    $ kubectl create -f <deployment_file>

    Args:

        deployment_file (str): File path to yaml deployment file.
    """
    with open(deployment_file, "r") as f:
        dep = yaml.safe_load(f)
        k8s_beta = client.AppsV1Api()
        resp = k8s_beta.create_namespaced_deployment(
            body=dep, namespace="default", pretty="true"
        )
        logger.info(f"Deployment {dep['metadata']['name']} done.")


def create_secret(secret_file):
    """Create a secret on k8s cluster.

    The same thing if you would do:

    $ kubectl create -f <secret_file>

    Args:

        secret_file (str): File path to yaml secret file.
    """
    with open(secret_file, "r") as f:
        dep = yaml.safe_load(f)
        k8s_beta = client.CoreV1Api()
        resp = k8s_beta.create_namespaced_secret(
            body=dep, namespace="default", pretty="true"
        )
        logger.info(f"Secret {dep['metadata']['name']} configured.")


def create_service(service_file):
    """Create a service on k8s cluster.

    The same thing if you would do:

    $ kubectl create -f <service_file>

    Args:

        service_file (str): File path to yaml service file.
    """
    with open(service_file, "r") as f:
        dep = yaml.safe_load(f)
        k8s_beta = client.CoreV1Api()
        resp = k8s_beta.create_namespaced_service(
            body=dep, namespace="default", pretty="true"
        )
        logger.info(f"Service {dep['metadata']['name']} configured.")


def create_storage(storage_file):
    """Create a storage on k8s cluster.

    The same thing if you would do:

    $ kubectl create -f <storage_file>

    Args:

        storage_file (str): File path to yaml storage file.
    """
    with open(storage_file, "r") as f:
        dep = yaml.safe_load(f)
        k8s_beta = client.CoreV1Api()
        resp = k8s_beta.create_namespaced_persistent_volume_claim(
            body=dep, namespace="default", pretty="true"
        )
        logger.info(f"Storage {dep['metadata']['name']} configured.")


def run_deploy(config_file):
    """Deploy a WP blog on Kubernetes cluster.

    Args:
        config_file (str): File path to the kube-config file.
    """
    config.load_kube_config(config_file=config_file)

    for secret in Secrets:
        create_secret(secret.value)

    for deploy in Deployments:
        create_deployment(deploy.value)

    for service in Services:
        create_service(service.value)

    for storage in Storage:
        create_storage(storage.value)

    v1 = client.CoreV1Api()
    logger.info("Waiting for Load Balancer's IP ...")
    watcher = Watch()
    resp = watcher.stream(
        v1.list_service_for_all_namespaces, watch=True, label_selector="app=blog"
    )
    for service in resp:
        logger.info("Still waiting for Load Balancer to get an external IP ...")
        if (
            service["object"].status.load_balancer.ingress
            and service["object"].spec.type == "LoadBalancer"
        ):
            logger.info(
                "Load Balancer", ip=service["object"].status.load_balancer.ingress[0].ip
            )
            watcher.stop()


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


def run_destroy(config_file):
    """Deploy a WP blog on Kubernetes cluster.

    Args:
        config_file (str): File path to the kube-config file.
    """
    config.load_kube_config(config_file=config_file)

    delete_deployment(namespace="default", label="app=blog")
    delete_secret(namespace="default", label="app=blog")

    for item in Services:
        with open(item.value, "r") as f:
            ser = yaml.safe_load(f)
            delete_service(namespace="default", name=ser["metadata"]["name"])

    delete_storage(namespace="default", label="app=blog")


@click.command(help="")
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=KUBE_CONFIG,
    help="Path to kube-config yaml file.",
    show_default=True,
)
def run(config):  # pragma: no cover
    """Main entry point."""
    destroy(config)


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=KUBE_CONFIG,
    help="Path to kube-config yaml file.",
    show_default=True,
)
def deploy(config):
    logger.info("Deploying WP blog on DigitalOcean Kubernetes cluster ...")
    run_deploy(config)


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=KUBE_CONFIG,
    help="Path to kube-config yaml file.",
    show_default=True,
)
def destroy(config):
    logger.info("Removing WP blog from Kubernetes cluster ...")
    run_destroy(config)


@click.group()
def cli():
    pass


cli.add_command(deploy)
cli.add_command(destroy)

if __name__ == "__main__":  # pragma: no cover
    cli()
