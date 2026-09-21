# GreenLake Activate CLI

The purpose of this is to help manage devices in HPE GreenLake Activate with an easy to use CLI interface.

# Setup

## Requirements

- Python 3.14 or newer
- An HPE GreenLake Activate API credential
- Network access to `activate.arubanetworks.com`

The CLI uses the following Python packages, which are installed automatically:

- Typer
- Requests
- Rich
- Python Dotenv

## Installation

Installing with `uv` is my recommendation.

[Install uv](https://docs.astral.sh/uv/getting-started/installation/) if it is not
already available.

To install the latest published package as a global command:

```sh
uv tool install greenlake-activate-cli
```

This installs the CLI in an isolated environment and makes `glcli` available from
any directory. If uv reports that its tool directory is not on your `PATH`, run:

```sh
uv tool update-shell
```

Restart your shell, then verify the installation:

```sh
glcli --help
```

To upgrade or remove the installed CLI:

```sh
uv tool upgrade greenlake-activate-cli
uv tool uninstall greenlake-activate-cli
```

### Install With Python and pip

Create a virtual environment, activate it, and install the project from the cloned
repository:

```sh
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

The `glcli` command is then available directly:

```sh
glcli --help
```

## Configure Credentials

Run the CLI `glcli configure` command.

```sh
glcli configure
```

You will be prompted to enter your GreenLake Activate API token. This text is hidden.

This command is essentially doing this:

```sh
mkdir -p ~/.config/greenlake-activate-cli
printf 'CREDENTIAL_1=your_api_key_here\n' \
	> ~/.config/greenlake-activate-cli/.env
chmod 600 ~/.config/greenlake-activate-cli/.env
```

Alternatively, you can set the environment variable manually:

```sh
export CREDENTIAL_1="your_api_key_here"
```

Credential sources are checked in this order:

1. A non-empty `CREDENTIAL_1` environment variable.
2. `$XDG_CONFIG_HOME/greenlake-activate-cli/.env`, when `XDG_CONFIG_HOME` is set.
3. `~/.config/greenlake-activate-cli/.env`.
4. `.env` in the current directory, retained for development and backward compatibility.

The configuration file format is:

```plain
CREDENTIAL_1=<your_api_key_here>
```

# Usage

Query inventory by serial number:

```sh
glcli query serial PHWLKAS02 PHWLKAS03
```

Query inventory by MAC address:

```sh
glcli query mac aa:bb:cc:00:11:22 dd:ee:ff:33:44:55
```

Query inventory by folder ID or folder name:

```sh
glcli query folder 5297450
glcli query folder SiteA-South
glcli query folder SiteA-South 5389522
```

Folder names are matched case-insensitively and exactly. Numeric values are treated
as folder IDs. Folder names are resolved through Activate before the inventory query;
unknown or ambiguous names are rejected. Folder queries currently accept positional
values only and do not support `--file`.

Serial numbers and MAC addresses can also be loaded from CSV or newline-delimited files:

```sh
glcli query serial --file serials.csv
glcli query mac --file mac_addresses.csv
```

The file reader uses the first column. Serial files may use a `serial`, `serialNumber`,
`serial_number`, `serial number`, or `sn` header.

Use `--verbose` for diagnostic logging:

```sh
glcli --verbose query serial PHWLKAS02
```

Exit codes are `0` for a complete result, `1` when no devices are returned, and
`2` when at least one requested identifier is missing.

Run the offline tests with:

```sh
uv run pytest
```
