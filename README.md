# reperio

<div align="center">

[![Build status](https://github.com/lewismc/reperio/workflows/build/badge.svg?branch=main&event=push)](https://github.com/lewismc/reperio/actions?query=workflow%3Abuild)
[![Python Version](https://img.shields.io/pypi/pyversions/reperio.svg)](https://pypi.org/project/reperio/)
[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/lewismc/reperio/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)

[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/lewismc/reperio/blob/main/.pre-commit-config.yaml)
[![Semantic Versions](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--versions-e10079.svg)](https://github.com/lewismc/reperio/releases)
[![License](https://img.shields.io/github/license/lewismc/reperio)](https://github.com/lewismc/reperio/blob/main/LICENSE)
![Coverage Report](assets/images/coverage.svg)

[Reperio](https://glosbe.com/la/en/reperio) is a visualization utility for [Apache Nutch](https://nutch.apache.org) CrawlDB, LinkDB and HostDB data structures.

Reperio is written in Python. It leverages [networkx](https://networkx.org/) and [Bokeh](https://docs.bokeh.org/en/latest/docs/user_guide/topics/graph.html) to generate network graph vizualizations.

</div>

## Quick start

Conda package manager is recommended. Create a conda environment.

```bash
conda create -n reperio python==3.10
```

Activate conda environment and install poetry

```bash
conda activate reperio
pip install poetry
```

Then you can run the client using the following command:

```bash
reperio --help
```

or with `Poetry`:

```bash
poetry run reperio --help
```

### Makefile usage

[`Makefile`](https://github.com/lewismc/reperio/blob/main/Makefile) contains a lot of functions for faster development.


<details>
<summary>Install all dependencies and pre-commit hooks</summary>
<p>

Install requirements:

```bash
make install
```

Pre-commit hooks coulb be installed after `git init` via

```bash
make pre-commit-install
```

</p>
</details>

<details>
<summary>Codestyle and type checks</summary>
<p>

Automatic formatting uses `ruff`.

```bash
make polish-codestyle

# or use synonym
make formatting
```

Codestyle checks only, without rewriting files:

```bash
make check-codestyle
```

> Note: `check-codestyle` uses `ruff` and `darglint` library

</p>
</details>

<details>
<summary>Code security</summary>
<p>

> If this command is not selected during installation, it cannnot be used.

```bash
make check-safety
```

This command launches `Poetry` integrity checks as well as identifies security issues with `Safety` and `Bandit`.

```bash
make check-safety
```

</p>
</details>

<details>
<summary>Tests with coverage badges</summary>
<p>

Run `pytest`

```bash
make test
```

</p>
</details>

<details>
<summary>All linters</summary>
<p>

Of course there is a command to run all linters in one:

```bash
make lint
```

the same as:

```bash
make check-codestyle && make test && make check-safety
```

</p>
</details>

<details>
<summary>Docker</summary>
<p>

```bash
make docker-build
```

which is equivalent to:

```bash
make docker-build VERSION=latest
```

Remove docker image with

```bash
make docker-remove
```

More information [about docker](https://github.com/Undertone0809/python-package-template/tree/main/%7B%7B%20cookiecutter.project_name%20%7D%7D/docker).

</p>
</details>

<details>
<summary>Cleanup</summary>
<p>
Delete pycache files

```bash
make pycache-remove
```

Remove package build

```bash
make build-remove
```

Delete .DS_STORE files

```bash
make dsstore-remove
```

Remove .mypycache

```bash
make mypycache-remove
```

Or to remove all above run:

```bash
make cleanup
```

</p>
</details>

## 🛡 License

[![License](https://img.shields.io/github/license/lewismc/reperio)](https://github.com/lewismc/reperio/blob/main/LICENSE)

This project is licensed under the terms of the `Apache Software License 2.0` license. See [LICENSE](https://github.com/lewismc/reperio/blob/main/LICENSE) for more details.

## 📃 Citation

```bibtex
@misc{reperio,
  author = {lewismc},
  title = {Reperio is a cvisualization utility for Apache Nutch data structures.},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/lewismc/reperio}}
}
```

## Credits [![🚀 Your next Python package needs a bleeding-edge project structure.](https://img.shields.io/badge/3PG-%F0%9F%9A%80-brightgreen)](https://github.com/Undertone0809/python-package-template)

This project was generated with [`3PG`](https://github.com/Undertone0809/3PG)
