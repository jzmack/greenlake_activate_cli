import pytest

from glcli.generate_allowlist import (
    AllowlistEntry,
    generate_cpsec_allowlist_command,
    generate_rap_allowlist_command,
    read_allowlist_entries_from_file,
)


def test_generate_cpsec_allowlist_command_includes_optional_description(tmp_path):
    assert generate_cpsec_allowlist_command(
        "AA:BB:CC:00:11:22", "campus", description="North site"
    ) == (
        'allowlist-db cpsec add mac-address AA:BB:CC:00:11:22 '
        'ap-group campus description "North site"'
    )


def test_generate_rap_allowlist_command_uses_ap_name_and_description():
    assert generate_rap_allowlist_command(
        "AA:BB:CC:00:11:22", "remote", "SN1", "North site"
    ) == (
        'allowlist-db rap add mac-address AA:BB:CC:00:11:22 ap-name SN1 '
        'ap-group remote description "North site"'
    )


def test_read_allowlist_csv_normalizes_required_fields(tmp_path):
    path = tmp_path / "allowlist.csv"
    path.write_text(
        " MAC_ADDRESS , AP_GROUP , SERIAL , description\n"
        "aa:bb:cc:00:11:22,remote,sn1,North site\n"
    )

    assert read_allowlist_entries_from_file(path, "rap") == [
        AllowlistEntry("AA:BB:CC:00:11:22", "remote", "SN1", "North site")
    ]


def test_read_allowlist_csv_requires_rap_serial_column(tmp_path):
    path = tmp_path / "allowlist.csv"
    path.write_text("mac_address,ap_group\naa:bb:cc:00:11:22,remote\n")

    with pytest.raises(ValueError, match="serial"):
        read_allowlist_entries_from_file(path, "rap")