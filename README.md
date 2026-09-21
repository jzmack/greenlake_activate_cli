# GreenLake Activate CLI

The purpose of this is to help manage devices in HPE GreenLake Activate with an easy to use CLI interface.

# Setup

Create `.env` file with GreenLake Activate token (may need to include instructions on how to get that). The only variable you need is `CREDENTIAL_1`.

Example `.env` file structure:

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
