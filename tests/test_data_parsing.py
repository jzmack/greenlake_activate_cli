from glcli.data_parsing import parse_inventory_response


def test_parser_handles_missing_additional_data():
    result = parse_inventory_response(
        '{"devices": [{"serialNumber": "SN1", "mac": "AA:BB"}, null]}'
    )

    assert result == [{
        "serial": "SN1",
        "mac": "AA:BB",
        "status": None,
        "folder": None,
        "folderId": None,
    }]