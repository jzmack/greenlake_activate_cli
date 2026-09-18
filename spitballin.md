# Commands:

This is a list of ideas for commands I'd like to implement.

## Query commands

`glcli query all` - returns all info for entire inventory, and maybe outputs to a file

---

`glcli query <device_name>` 

`glcli query <serial_number>` 

`glcli query <mac_address>` 

Examples:

```sh
glcli query PHQVKSM4FM PHQVKS303H
glcli query aa:bb:cc:00:11:22 dd:ee:ff:11:22:33 
glcli query south-ap01 south-ap02
```

---

### Query-only options

`-o` `--output` <FILENAME> - output to a file/csv

##
