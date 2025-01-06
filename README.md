# MOT Data Wrangling

A collection of tools to work with MOT data from various of sources.

## Overview

There is currently support for:

- **DVSA MOT History API** via the command line interface `dvsa-mot-history-api`.

    - Looking up the MOT history for a single vehicle by VRM or VIN.

    - Downloading bulk data and converting to Parquet format.

## Getting started

This package uses [`uv`](https://docs.astral.sh/uv/) to manage dependencies and installation. Make sure you install it before continuing.

To access the DVSA MOT History API, you will need to [register for credentials](https://documentation.history.mot.api.gov.uk).
You will be provided with a `CLIENT_SECRET`, `API_KEY`, `SCOPE_URL`, `TOKEN_URL` and `API_URL`.
These should be kept secret and placed inside a `.env` file at the root of this repository.
See [`.env.sample`](./.env.sample) for an example of how that file should look.

Once you have installed `uv`, obtained API credientials and created a `.env` file, try running the following from a command line within your local copy of the repository:

```bash
uv run dvsa-mot-history-api --help
```

## Development

Python code for the command line interface (CLI) is stored inside [`src/mot_data`](./src/mot_data).
Each command (for example, [`dvsa-mot-history-api`](./src/mot_data/dvsa_mot_history_api)) is stored in its own directory, with the entry points to the CLI defined in `cli.py`.
The commands are registered as scripts inside [`pyproject.toml`](./pyproject.toml), which causes `uv` to make them runnable at the command line.

Testing, type checking, linting and formatting of source code are performed using `pytest`, `mypy` and `ruff`.
You can run all of these automatically using:

```bash
uv run just all
```

or to list the individual commands:

```bash
uv run just
```

## Contributors

- [James Thomas](https://github.com/jatonline), Jean Golding Institute, University of Bristol

## Acknowledgements

This software has been developed as part of the [CARS Project](https://cars-project.github.io/), a collaboration between [University of Leeds](https://www.leeds.ac.uk/) and [University of Bristol](https://www.bristol.ac.uk/) and funded by [ADR UK](https://www.adruk.org/).

This software uses the DVSA MOT History API, however it is neither affialiated with nor endorsed by the DVSA or Department for Transport.

Supported by the [Jean Golding Institute](https://www.bristol.ac.uk/golding/).

## License

The source code in this repository is licensed under the MIT License.
