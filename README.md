# GreenLake Activate CLI

The purpose of this is to help manage devices in HPE GreenLake Activate with an easy to use CLI interface.

# Setup

Create `.env` file with GreenLake Activate token (may need to include instructions on how to get that). The only variable you need is `CREDENTIAL_1`.

Example `.env` file structure:

```plain
CREDENTIAL_1=<your_api_key_here>
```

# Usage

Current example usage with made up S/Ns:

```sh
glcli query PHWLKAS02 PHWLKAS03
```

Or:

```sh
uv run glcli query PHWLKAS02 PHWLKAS03
```
