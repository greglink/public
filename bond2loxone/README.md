# bond2loxone

A Python command-line tool that automatically discovers devices and groups on a Bond Bridge device via its local API, then generates a Loxone `.LxAddon` file containing Virtual Outputs and Virtual Inputs to enable complete integration with Loxone home automation systems.

## Features

- **Automated Discovery**: Query Bond Bridge to find all devices and groups
- **Comprehensive Support**: Handle all discovered device types and their actions
- **Extensibility**: Support custom device mappings via configuration files
- **User-Friendly**: Clear CLI output showing what was discovered and how it's being handled
- **Unknown Action Handling**: Generate test cases for unknown actions with guidance for users
- **State Feedback**: Automatic Virtual Input generation for readable state endpoints

## Installation

```bash
pip install .
```

## Usage

```bash
bond2loxone --host <bond_address> --token <api_token> --config bond2loxone/examples/default_mapping.json
```

### Arguments

- `--host`: Bond Bridge network address (IP or mDNS name like `ZZBL12345.local`)
- `--token`: Bond local API token for authentication
- `--out <filename>`: Output .LxAddon filename (default: bond2loxone.LxAddon)
- `--config <json_file>`: Custom device mapping configuration
- `--include-state`: Query and include state information (default: true)
- `--state-poll-interval <sec>`: Polling interval for state updates (default: 30)
- `--emit-intermediate <dir>`: Save intermediate files for debugging
- `--timeout <seconds>`: HTTP timeout (default: 3.0)
- `--verbose, -v`: Increase verbosity (can be repeated: -v, -vv, -vvv)
- `--quiet, -q`: Suppress non-error output
- `--dry-run`: Show what would be generated without creating files

## Configuration

You can provide a JSON configuration file to customize device mappings. See `examples/` for details.

## End Result

Once parsed, one or more custom .LxAddon files will be generated, specifically for your Bond Bridge, with all devices supported by default

<img src="examples/example_output/Example%20of%20Imported%20Template.jpg" alt="Example of Imported Custom .LxAddon File" width="1024">
