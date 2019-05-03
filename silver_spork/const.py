"""Project constants."""

from enum import Enum


KUBE_CONFIG = "k8s/kubeconfig.yaml"


class Deployments(Enum):
    mysql = "k8s/deployments/mysql.yaml"
    wp = "k8s/deployments/wp.yaml"


class Services(Enum):
    wp_service = "k8s/services/wp.yaml"
    mysql_service = "k8s/services/wordpress-mysql.yaml"


class Storage(Enum):
    pvc_mysql = "k8s/storage/pvc-mysql.yaml"
    pvc_wp = "k8s/storage/pvc-wp.yaml"


class Secrets(Enum):
    mysql = "k8s/secrets/mysql.yaml"
