"""Entry point."""

from kubernetes import client, config, utils


import click
import structlog
import yaml


TESTING = False
logger = structlog.get_logger(__name__)


def main(config_file):
    """.

    Args:
        config_file (str): File path to the kube-config file.
    """

    # See https://github.com/kubernetes-client/python-base/blob/1d5231cee6d0674b958ad429b60dda39363a4dc1/config/kube_config.py#L612
    config.load_kube_config(config_file=config_file)

    k8s_client = client.ApiClient()
    import pdb

    pdb.set_trace()
    # utils.create_from_yaml(k8s_client, "nginx-deployment.yaml")
    # k8s_api = client.ExtensionsV1beta1Api(k8s_client)
    # deps = k8s_api.read_namespaced_deployment("nginx-deployment", "default")
    # print("Deployment {0} created".format(deps.metadata.name))


@click.command(help="")
@click.option(
    "--config",
    type=click.Path(exists=True),
    default="k8s/kubeconfig.yaml",
    help="Path to kube-config yaml file.",
    show_default=True,
)
@click.option(
    "--testing",
    is_flag=True,
    default=False,
    type=bool,
    help="If set it will run in testing mode.",
    show_default=True,
)
def run(testing, config):  # pragma: no cover
    """."""
    if testing:
        global TESTING
        TESTING = True
    main(config)


if __name__ == "__main__":  # pragma: no cover
    run()
