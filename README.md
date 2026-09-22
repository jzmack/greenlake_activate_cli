# GreenLake Activate CLI

The purpose of this is to help manage devices in HPE GreenLake Activate with an easy to use CLI interface. This tool uses the available API calls that HPE GreenLake Activate exposes for manging devices

## Features

- Query Activate inventory by:
    - device name
    - mac address
    - serial number
    - folder name
    - folder id
- Move devices between folders
- Create folders in Activate
- Create provisioning rules for folders (WIP)
- Generate CLI commands for allowlist entries (WIP)

## Requirements

- Python 3.12 or newer
- An HPE GreenLake Activate API credential
- Network access to `activate.arubanetworks.com`

## Installation

I recommend installing this package with `uv`. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) if it is not already available.

Installing uv on Linux/Mac:
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Installing uv on Windows:

```ps
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

To install the latest published package as a global command:

```sh
uv tool install greenlake-activate-cli
```

Verify the installation:

```sh
glcli --version
```

To upgrade or remove the installed CLI:

```sh
uv tool upgrade greenlake-activate-cli
uv tool uninstall greenlake-activate-cli
```

### Install With Python and pip

Creating a virtual environment and installing the package:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install greenlake-activate-cli
```

The `glcli` command is then available from the venv:

```sh
glcli --version
```

## Configuration 

Run the CLI `glcli configure` command.

```sh
glcli configure
```

You will be prompted to enter (paste) in your GreenLake Activate API token. This text is hidden.

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
```

Move a device by serial number or MAC address:

```sh
glcli move PHWLKAS02 SiteA-South
glcli move aa:bb:cc:00:11:22 5297450
```

Move multiple devices from a file:

```sh
glcli move serials serials.csv SiteA-South
glcli move macs mac_addresses.csv 5297450
```

Create a new folder in Activate:

```sh
glcli create folder Jake_test2
```

Serial numbers and MAC addresses can also be loaded from CSV or newline-delimited files:

```sh
glcli query serial --file serials.csv
glcli query mac --file mac_addresses.csv
```

Use `--verbose` for diagnostic logging:

```sh
glcli --verbose query serial PHWLKAS02
```

Exit codes are `0` for a complete result, `1` when no devices are returned, and
`2` when at least one requested identifier is missing.

## Troubleshooting

The installation with uv installs this package in an isolated environment and makes `glcli` available to run from any directory. If uv reports that its tool directory is not on your `PATH`, run:

```sh
uv tool update-shell
```

To run the tests;

```sh
uv run pytest
```

# References

- [GreenLake Activate API Documentation](https://support.hpe.com/hpesc/public/docDisplay?docId=a00120791en_us&page=GUID-264278DA-9B2B-4E1E-9DED-596562E2CEF4.html)
