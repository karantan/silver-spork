# Silver Spork
Sandbox for deploying blogs on a DigitalOcean Kubernetes cluster. The main purpose of
this project is to have a small code base so that we can test different options regarding
kubernetes objects (.yaml files) and python kubernetes library.

## Installation

You need to have `pipenv` installed first, then just simply type:

```bash
$ git clone https://github.com/karantan/silver-spork
$ make install
```

Read `Makefile` for additional commands.

## Run

To deploy a blog on a kubernetes cluster you first need to create a kubernetes cluster.
Once this is done, download the `<my-project>-kubeconfig.yaml` to `k8s` folder and rename
it to `kubeconfig.yaml`. If you don't you won't be able to use commands from `Makefile`.

Then to deploy a blog type:

```bash
$ make deploy
```

You will be asked for a domain. This is just to create a specific [namespace](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)
for this blog. Let's say you have a domain "foo.com", you will need to type `foo-com`
because of the namespace restrictions.


To see which blogs have you deployed type:

```bash
$ make list-blogs
```

And to remove a blog type:

```bash
$ make destroy
```

You will be asked to enter the domain of the blog you want to remove.

## Contribute


- Issue Tracker: github.com/karantan/silver-spork/issues
- Source Code: github.com/karantan/silver-spork


## Support


If you are having issues, please let us know.
