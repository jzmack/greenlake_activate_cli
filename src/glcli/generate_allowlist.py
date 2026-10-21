import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AllowlistEntry:
    mac_address: str
    ap_group: str
    serial: str = ""
    description: str = ""


def read_allowlist_entries_from_file(path: Path, provision_type: str) -> list[AllowlistEntry]:
    """Read allowlist entries from a header-based CSV file."""
    if provision_type not in {"cap", "rap"}:
        raise ValueError(f"Unsupported allowlist type: {provision_type}")

    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError(f"File is empty or missing a header: {path}")

        normalized_headers = [header.strip().casefold() for header in reader.fieldnames]
        if len(set(normalized_headers)) != len(normalized_headers):
            raise ValueError("CSV contains duplicate column names")

        required_headers = {"mac_address", "ap_group"}
        if provision_type == "rap":
            required_headers.add("serial")
        missing_headers = required_headers - set(normalized_headers)
        if missing_headers:
            raise ValueError(f"CSV is missing required column(s): {', '.join(sorted(missing_headers))}")

        entries = []
        for row_number, values in enumerate(reader, start=2):
            row = {
                header: (value or "").strip()
                for header, value in zip(normalized_headers, values.values())
            }
            if not any(row.values()):
                continue

            required_values = ["mac_address", "ap_group"]
            if provision_type == "rap":
                required_values.append("serial")
            missing_values = [column for column in required_values if not row.get(column)]
            if missing_values:
                raise ValueError(
                    f"CSV row {row_number} is missing required value(s): {', '.join(missing_values)}"
                )

            entries.append(
                AllowlistEntry(
                    mac_address=row["mac_address"].upper(),
                    ap_group=row["ap_group"],
                    serial=row.get("serial", "").upper(),
                    description=row.get("description", ""),
                )
            )

    if not entries:
        raise ValueError(f"No allowlist entries found in {path}")
    return entries


def generate_cpsec_allowlist_command(
    mac_address:str,
    ap_group:str,
    description="",
    ap_name=""
) -> str:

    if description != "" and ap_name != "":
        return f'allowlist-db cpsec add mac-address {mac_address} ap-name {ap_name} ap-group {ap_group} description "{description}"'
    if ap_name != "":
        return f'allowlist-db cpsec add mac-address {mac_address} ap-name {ap_name} ap-group {ap_group}'
    if description != "":
        return f'allowlist-db cpsec add mac-address {mac_address} ap-group {ap_group} description "{description}"'
    return f"allowlist-db cpsec add mac-address {mac_address} ap-group {ap_group}"

def generate_rap_allowlist_command(
    mac_address:str,
    ap_group:str,
    ap_name:str,
    description:str="",
) -> str:

    if description != "" and ap_name != "":
        return f'allowlist-db rap add mac-address {mac_address} ap-name {ap_name} ap-group {ap_group} description "{description}"'
    if ap_name != "":
        return f'allowlist-db rap add mac-address {mac_address} ap-name {ap_name} ap-group {ap_group}'
    if description != "":
        return f'allowlist-db rap add mac-address {mac_address} ap-group {ap_group} description "{description}"'
    return f"allowlist-db rap add mac-address {mac_address} ap-group {ap_group}"
