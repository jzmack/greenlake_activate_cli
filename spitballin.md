# Commands:

This is a list of ideas for commands I'd like to implement.

## Inventory Query commands

`glcli query all` - returns all info for entire inventory, and maybe outputs to a file

---

Querying devices examples:

```sh
glcli query serial PHQVKSM4FM PHQVKS303H
glcli query mac aa:bb:cc:00:11:22 dd:ee:ff:11:22:33
glcli query name south-ap01 south-ap02
```

Querying folder example:

`glcli query folder site_1` - return devices in that folder

---

### Query-only options

`-f` `--file` <FILENAME> - read a file of Serial Numbers

`-o` `--output` <FILENAME> - output to a file/csv


## Device move commands

`glcli move <MAC_ADDRESSES> <FOLDER_NAME/ID>` - move single device to a folder
`glcli move list <filename> <FOLDER_NAME>` - move list of devices to folder

## Create commands

`glcli create folder <FOLDER_NAME>` - return code, ID, other data
`glcli create rule <FOLDER NAME>` - not sure about this one yet
