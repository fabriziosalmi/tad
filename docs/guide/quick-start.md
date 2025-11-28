# Quick Start

Get TAD running in under 5 minutes!

## Installation

```bash
git clone https://github.com/fabriziosalmi/tad.git
cd tad
./install.sh
```

## Launch TAD

```bash
./tad
```

Or with Python:

```bash
python -m tad.main
```

## Basic Commands

### Send Messages
Just type and press Enter:
```
> Hello everyone!
```

### View Connected Peers
```
> /peers
```

### Create a Channel
```
> /create #mychannel
```

### Switch Channels
```
> /switch #mychannel
```

### List All Channels
```
> /channels
```

### Get Help
```
> /help
```

### Exit
```
> /quit
```

## Creating Your First Private Channel

```bash
> /create-private #secret mypassword123
> /switch #secret
> This message is encrypted!
```

## What's Next?

- [Full User Guide](/guide/user-guide) - All commands and features
- [Channels Guide](/guide/channels) - Working with channels
- [Private Channels](/guide/private-channels) - End-to-end encryption
- [Troubleshooting](/guide/troubleshooting) - Common issues

## Tips

💡 **Tip**: TAD works on local networks only - make sure all devices are on the same Wi-Fi/LAN

💡 **Tip**: Use `/export` to backup your data before updates

💡 **Tip**: Check `/peers` to see who's online
