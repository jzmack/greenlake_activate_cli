# Commands:

This is a list of ideas for commands I'd like to implement.

## Inventory Query commands

`glcli query all` - returns all info for entire inventory, and maybe outputs to a file

---

`glcli query <device_names>` 

`glcli query <serial_numbers>` 

`glcli query <mac_addresses>` 

Examples:

```sh
glcli query PHQVKSM4FM PHQVKS303H
glcli query aa:bb:cc:00:11:22 dd:ee:ff:11:22:33
glcli query south-ap01 south-ap02
```

---

### Query-only options

`-f` `--file` <FILENAME> - read a file of Serial Numbers
`-o` `--output` <FILENAME> - output to a file/csv


## Folder Query Commands

## Device move commands

`glcli move <MAC_ADDRESSES> <FOLDER_NAME/ID>`
`glcli move list <filename> <FOLDER_NAME>`
