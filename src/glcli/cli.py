import logging
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import typer
from glcli.activate_login import create_activate_session, load_credentials, save_user_credential
from glcli.data_parsing import parse_inventory_response
from glcli.query_inventory import query_inventory, read_identifiers_from_file
from glcli.query_folder import resolve_folder_ids
from glcli.query_rule import query_rule
from glcli.move_device import move_device, resolve_move_macs, MAC_PATTERN
from glcli.create_folder import create_folder
from glcli.create_rule import create_provision_rule
from glcli.display_data import display_inventory_sn, display_rules
from glcli.generate_allowlist import (
    AllowlistEntry,
    generate_cpsec_allowlist_command,
    generate_rap_allowlist_command,
    read_allowlist_entries_from_file,
)
from rich.logging import RichHandler
from rich import print

logger = logging.getLogger(__name__)
app = typer.Typer(help="Interact with HPE GreenLake Activate via CLI.")
query_app = typer.Typer(help="Query Activate inventory and provisioning rules.")
app.add_typer(query_app, name="query")
rule_app = typer.Typer(help="Query provisioning rules for one folder.")
query_app.add_typer(rule_app, name="rule")
create_app = typer.Typer(help="Create resources in Activate.")
app.add_typer(create_app, name="create")
create_rule_app = typer.Typer(help="Create a provisioning rule for one folder.")
create_app.add_typer(create_rule_app, name="rule")
generate_allowlist_app = typer.Typer(help="Generate allowlist commands from a folder or CSV file.")
app.add_typer(generate_allowlist_app, name="generate-allowlist")
cap_allowlist_app = typer.Typer(help="Generate campus AP allowlist commands.")
generate_allowlist_app.add_typer(cap_allowlist_app, name="cap")
rap_allowlist_app = typer.Typer(help="Generate remote AP allowlist commands.")
generate_allowlist_app.add_typer(rap_allowlist_app, name="rap")

def setup_logging(verbose: bool):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s" if verbose else "%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, show_path=verbose)],
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_version() -> str:
    try:
        return version("greenlake-activate-cli")
    except PackageNotFoundError:
        return "dev"

def show_version(value:bool) -> None:
    if value:
        typer.echo(f"glcli {get_version()}")
        raise typer.Exit()

def _load_credential() -> str:
    try:
        return load_credentials()
    except RuntimeError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

def _query(identifier_type: str, identifiers: list[str], file: Path | None = None) -> None:
    if file is not None:
        identifiers = read_identifiers_from_file(file, identifier_type)

    identifiers = [identifier.strip().upper() for identifier in identifiers if identifier.strip()]
    if not identifiers:
        raise typer.BadParameter("At least one identifier is required")

    identifiers = list(dict.fromkeys(identifiers))
    credential = _load_credential()
    try:
        session = create_activate_session(credential)
        query_result, missing = query_inventory(session, identifier_type, identifiers)
    finally:
        if "session" in locals():
            session.close()

    extracted_data = parse_inventory_response(query_result)

    if missing:
        print(f"Not found: ({len(missing)}): {', '.join(missing)}")

    display_inventory_sn(extracted_data)

    if not extracted_data:
        raise typer.Exit(code=1)
    if missing:
        raise typer.Exit(code=2)


def _query_folder(values: list[str]) -> None:
    values = [value.strip() for value in values if value.strip()]
    if not values:
        raise typer.BadParameter("At least one folder ID or name is required")

    values = list(dict.fromkeys(values))
    credential = _load_credential()
    session = None
    try:
        session = create_activate_session(credential)
        try:
            folder_ids = resolve_folder_ids(session, values)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        query_result, missing = query_inventory(session, "folder", folder_ids)
    finally:
        if session is not None:
            session.close()

    extracted_data = parse_inventory_response(query_result)
    display_inventory_sn(extracted_data)

    if not extracted_data:
        raise typer.Exit(code=1)


def _query_rules(folder_value: str, resolve_name: bool) -> None:
    folder_value = folder_value.strip()
    if not folder_value:
        raise typer.BadParameter("A folder ID or name is required")

    credential = _load_credential()
    session = None
    try:
        session = create_activate_session(credential)
        if resolve_name:
            try:
                folder_ids = resolve_folder_ids(session, [folder_value])
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc
            folder_id = folder_ids[0]
        else:
            folder_id = folder_value
        rules = query_rule(session, folder_id)
    except RuntimeError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    finally:
        if session is not None:
            session.close()

    display_rules(rules)


def _move(identifier_type: str, identifiers: list[str], destination: str) -> None:
    identifiers = [identifier.strip().upper() for identifier in identifiers if identifier.strip()]
    destination = destination.strip()
    if not identifiers:
        raise typer.BadParameter("At least one identifier is required")
    if not destination:
        raise typer.BadParameter("A destination folder is required")

    identifiers = list(dict.fromkeys(identifiers))
    credential = _load_credential()
    session = None
    try:
        session = create_activate_session(credential)
        mac_addresses, unresolved = resolve_move_macs(session, identifier_type, identifiers)
        if unresolved:
            typer.echo(f"Not found or missing MAC: {', '.join(unresolved)}", err=True)
        if not mac_addresses:
            raise typer.Exit(code=1)
        move_device(session, mac_addresses, destination)
    finally:
        if session is not None:
            session.close()

    if unresolved:
        raise typer.Exit(code=2)


def _allowlist_command(entry: AllowlistEntry, provision_type: str) -> str:
    if provision_type == "cap":
        return generate_cpsec_allowlist_command(
            entry.mac_address,
            entry.ap_group,
            entry.description,
        )
    return generate_rap_allowlist_command(
        entry.mac_address,
        entry.ap_group,
        entry.serial,
        entry.description,
    )


def _preview_and_confirm_allowlist(
    entries: list[AllowlistEntry],
    provision_type: str,
    text_file: bool,
) -> None:
    commands = [_allowlist_command(entry, provision_type) for entry in entries]
    output_path = Path("allowlist_commands.txt") if text_file else None
    typer.echo("Allowlist commands to generate:")
    for entry in entries:
        details = f"  MAC: {entry.mac_address} | AP group: {entry.ap_group}"
        if provision_type == "rap":
            details += f" | AP name: {entry.serial}"
        if entry.description:
            details += f" | Description: {entry.description}"
        typer.echo(details)

    if output_path is None:
        confirmation = "Generate these allowlist commands?"
    else:
        overwrite_note = " (overwrite existing file)" if output_path.exists() else ""
        confirmation = f"Write commands to {output_path}{overwrite_note}?"
    if not typer.confirm(confirmation, default=False):
        typer.echo("Allowlist command generation cancelled.")
        return

    if output_path is not None:
        try:
            output_path.write_text("\n".join(commands) + "\n", encoding="utf-8")
        except OSError as exc:
            typer.echo(f"Error writing {output_path}: {exc}", err=True)
            raise typer.Exit(code=1) from exc
        typer.echo(f"Wrote {len(commands)} command(s) to {output_path}")
        return

    typer.echo("Generated allowlist commands:")
    for command in commands:
        typer.echo(command)


def _generate_allowlist_from_file(path: Path, provision_type: str, text_file: bool) -> None:
    try:
        entries = read_allowlist_entries_from_file(path, provision_type)
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    _preview_and_confirm_allowlist(entries, provision_type, text_file)


def _generate_allowlist_from_folder(
    folder_name: str,
    provision_type: str,
    description: str,
    text_file: bool,
) -> None:
    folder_name = folder_name.strip()
    if not folder_name:
        raise typer.BadParameter("A folder name is required")

    credential = _load_credential()
    session = None
    try:
        session = create_activate_session(credential)
        try:
            folder_ids = resolve_folder_ids(session, [folder_name])
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc

        inventory_response, _ = query_inventory(session, "folder", folder_ids)
        rules = query_rule(session, folder_ids[0])
    except RuntimeError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    finally:
        if session is not None:
            session.close()

    devices = parse_inventory_response(inventory_response)
    if not devices:
        raise typer.BadParameter(f"No devices found in folder '{folder_name}'")

    required_fields = ("mac", "serial") if provision_type == "rap" else ("mac",)
    entries = []
    for device in devices:
        missing = [field for field in required_fields if not device.get(field)]
        if missing:
            raise typer.BadParameter(
                f"A device in folder '{folder_name}' is missing required "
                f"inventory data: {', '.join(missing)}"
            )
        entries.append(
            AllowlistEntry(
                mac_address=str(device["mac"]).strip().upper(),
                ap_group="",
                serial=str(device.get("serial") or "").strip().upper(),
                description=description.strip(),
            )
        )

    ap_groups = list(
        dict.fromkeys(
            str(rule.get("apGroup") or "").strip()
            for rule in rules
            if str(rule.get("apGroup") or "").strip()
        )
    )
    if len(ap_groups) > 1:
        raise typer.BadParameter(
            f"Folder '{folder_name}' has multiple AP groups defined: {', '.join(ap_groups)}"
        )
    if ap_groups:
        ap_group = ap_groups[0]
    else:
        typer.echo(f"No AP group is defined for folder '{folder_name}'.")
        ap_group = typer.prompt("AP group").strip()
        if not ap_group:
            raise typer.BadParameter("An AP group is required")

    entries = [
        AllowlistEntry(
            mac_address=entry.mac_address,
            ap_group=ap_group,
            serial=entry.serial,
            description=entry.description,
        )
        for entry in entries
    ]
    _preview_and_confirm_allowlist(entries, provision_type, text_file)


@cap_allowlist_app.command("folder")
def generate_cap_allowlist_from_folder(
    folder_name: str = typer.Argument(..., metavar="FOLDER_NAME"),
    description: str = typer.Option("", "--description", help="Optional command description."),
    text_file: bool = typer.Option(
        False,
        "--text",
        help="Write commands to allowlist_commands.txt instead of printing them.",
    ),
) -> None:
    """Generate campus AP allowlist commands for devices in a folder."""
    _generate_allowlist_from_folder(folder_name, "cap", description, text_file)


@cap_allowlist_app.command("file")
def generate_cap_allowlist_from_file(
    file_path: Path = typer.Argument(..., metavar="FILE_PATH"),
    text_file: bool = typer.Option(
        False,
        "--text",
        help="Write commands to allowlist_commands.txt instead of printing them.",
    ),
) -> None:
    """Generate campus AP allowlist commands from a CSV file."""
    _generate_allowlist_from_file(file_path, "cap", text_file)


@rap_allowlist_app.command("folder")
def generate_rap_allowlist_from_folder(
    folder_name: str = typer.Argument(..., metavar="FOLDER_NAME"),
    description: str = typer.Option("", "--description", help="Optional command description."),
    text_file: bool = typer.Option(
        False,
        "--text",
        help="Write commands to allowlist_commands.txt instead of printing them.",
    ),
) -> None:
    """Generate remote AP allowlist commands for devices in a folder."""
    _generate_allowlist_from_folder(folder_name, "rap", description, text_file)


@rap_allowlist_app.command("file")
def generate_rap_allowlist_from_file(
    file_path: Path = typer.Argument(..., metavar="FILE_PATH"),
    text_file: bool = typer.Option(
        False,
        "--text",
        help="Write commands to allowlist_commands.txt instead of printing them.",
    ),
) -> None:
    """Generate remote AP allowlist commands from a CSV file."""
    _generate_allowlist_from_file(file_path, "rap", text_file)


@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debugging output to console."),
    version: bool = typer.Option(False, "--version", callback=show_version, is_eager=True, help="Show the installed version.")
) -> None:
    setup_logging(verbose)


@app.command("configure")
def configure() -> None:
    """Save the Activate credential for future commands."""
    credential = typer.prompt("GreenLake Activate credential", hide_input=True, confirmation_prompt=True)
    try:
        config_path = save_user_credential(credential)
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    print(f":heavy_check_mark:  Credential saved to {config_path}")


@create_app.command("folder")
def create_folder_command(
    folder_name: str = typer.Argument(..., metavar="FOLDER_NAME"),
) -> None:
    """Create a folder in Activate."""
    folder_name = folder_name.strip()
    if not folder_name:
        raise typer.BadParameter("A folder name is required")

    credential = _load_credential()
    session = None
    try:
        session = create_activate_session(credential)
        try:
            created_folder = create_folder(session, folder_name)
        except (RuntimeError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc
    finally:
        if session is not None:
            session.close()

    print(f"Created folder '{created_folder.name}' with ID {created_folder.folder_id}")


def _prompt_provision_type() -> str:
    while True:
        choice = typer.prompt("Provision type (cap/rap)").strip().casefold()
        if choice == "cap":
            return "iap_to_cap"
        if choice == "rap":
            return "iap_to_rap"
        typer.echo("Choose 'cap' or 'rap'.", err=True)


def _create_rule(folder_value: str, resolve_name: bool) -> None:
    rule_name = typer.prompt("Rule name").strip()
    provision_type = _prompt_provision_type()
    controller_ip = typer.prompt("Controller IP").strip()
    ap_group = typer.prompt("AP group").strip()
    if not all((rule_name, controller_ip, ap_group)):
        raise typer.BadParameter("Rule name, controller IP, and AP group are required")

    folder_value = folder_value.strip()
    if not folder_value:
        raise typer.BadParameter("A folder ID or name is required")

    credential = _load_credential()
    session = None
    try:
        session = create_activate_session(credential)
        if resolve_name:
            try:
                folder_ids = resolve_folder_ids(session, [folder_value])
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc
            folder_id = folder_ids[0]
        else:
            folder_id = folder_value

        typer.echo("\nProvisioning rule to create:")
        typer.echo(f"  Rule name: {rule_name}")
        typer.echo(f"  Folder ID: {folder_id}")
        typer.echo(f"  Provision type: {provision_type}")
        typer.echo(f"  Controller: {controller_ip}")
        typer.echo(f"  AP group: {ap_group}")
        if not typer.confirm("Create this provisioning rule?", default=False, abort=False):
            typer.echo("Rule creation cancelled.")
            return

        created_rule = create_provision_rule(
            session,
            rule_name,
            folder_id,
            provision_type,
            controller_ip,
            ap_group,
        )
    except RuntimeError as exc:
        typer.echo(f"Error: {exc}", err=True)
        typer.echo("Does a provisioning rule already exist?")
        raise typer.Exit(code=1) from exc
    finally:
        if session is not None:
            session.close()

    print(f"Created provisioning rule '{created_rule.name}' with ID {created_rule.rule_id}")


@create_rule_app.command("folder-id")
def create_rule_by_folder_id(
    folder_id: str = typer.Argument(..., metavar="FOLDER_ID"),
) -> None:
    """Create a provisioning rule for a folder ID."""
    _create_rule(folder_id, resolve_name=False)


@create_rule_app.command("folder-name")
def create_rule_by_folder_name(
    folder_name: str = typer.Argument(..., metavar="FOLDER_NAME"),
) -> None:
    """Create a provisioning rule for a folder name."""
    _create_rule(folder_name, resolve_name=True)


@app.command("move")
def move(
    arguments: list[str] = typer.Argument(..., metavar="MOVE_ARGUMENT"),
) -> None:
    """Move a device or a file of devices to an Activate folder.

    Forms:
        move IDENTIFIER DESTINATION
        move serials FILE DESTINATION
        move macs FILE DESTINATION

    examples:
        move SERIALNO12 Site_A
        move AA:BB:CC:DD:EE:FF Site_B
        move serials ./serials.csv Site_C
        move macs ./macs.csv Site_D

    """
    if arguments[0] in {"serials", "macs"}:
        if len(arguments) != 3:
            raise typer.BadParameter("Expected: move serials|macs FILENAME DESTINATION")
        identifier_type = "serial" if arguments[0] == "serials" else "mac"
        try:
            identifiers = read_identifiers_from_file(Path(arguments[1]), identifier_type)
        except (OSError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc
        _move(identifier_type, identifiers, arguments[2])
        return

    if len(arguments) != 2:
        raise typer.BadParameter("Expected: move IDENTIFIER DESTINATION")
    identifier_type = "mac" if MAC_PATTERN.fullmatch(arguments[0].strip()) else "serial"
    _move(identifier_type, [arguments[0]], arguments[1])


@query_app.command("serial")
def query_serial(
    serials: list[str] | None = typer.Argument(None, metavar="SERIAL"),
    file: Path | None = typer.Option(None, "--file", "-f", help="CSV or text file containing serial numbers."),
) -> None:
    """Query inventory by serial number(s)."""
    _query("serial", serials or [], file)


@query_app.command("mac")
def query_mac(
    macs: list[str] | None = typer.Argument(None, metavar="MAC"),
    file: Path | None = typer.Option(None, "--file", "-f", help="CSV or text file containing MAC addresses."),
) -> None:
    """Query inventory by MAC address(es)."""
    _query("mac", macs or [], file)


@query_app.command("folder")
def query_folder(
    folders: list[str] = typer.Argument(..., metavar="FOLDER_ID_OR_NAME"),
) -> None:
    """Query inventory by folder ID or folder name."""
    _query_folder(folders)


@rule_app.command("folder-id")
def query_rule_by_folder_id(
    folder_id: str = typer.Argument(..., metavar="FOLDER_ID"),
) -> None:
    """Query provisioning rules by folder ID."""
    _query_rules(folder_id, resolve_name=False)


@rule_app.command("folder-name")
def query_rule_by_folder_name(
    folder_name: str = typer.Argument(..., metavar="FOLDER_NAME"),
) -> None:
    """Query provisioning rules by folder name."""
    _query_rules(folder_name, resolve_name=True)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
