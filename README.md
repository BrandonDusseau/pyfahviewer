# PyFahViewer - A Folding@Home Wall Display

[![Build Status](https://travis-ci.com/BrandonDusseau/pyfahviewer.svg?branch=master)](https://travis-ci.com/BrandonDusseau/pyfahviewer)

This application serves as a wall display for viewing your Folding@Home team ranking and work unit progress.

## Requirements

 * Python 3.5+
 * `virtualenv` (`pip install virtualenv`)

## Getting Started

**NOTE:** You should not use this application if your Folding@Home control port is exposed to the Internet. This project does not support password authentication at this time.

1. Copy `config.example.json` to `config.json` and input your configuration parameters. See the _Configuration_ section for details.

2. Set up your Folding@Home clients to allow access from any IP.

   1. From the Folding@Home client, go to Configure > Remote Access.

   2. Under **Passwordless IP Address Restriction** set value `0.0.0.0/0` and **Save**.

3. Install dependencies and set up the virtual environment:
    ```bash
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

4. Start the application while inside the virtualenv:
    ```bash
    python pyfahviewer/main.py // On some systems it may be necessary to change `python` to `python3` for 3.x.
    ```

5. Navigate to `http://localhost:5000` in your browser.

6. When you're finished, you can press Ctrl+C in the terminal to stop the server, then run `deactivate` to return to your normal shell.

## Configuration

The application uses a JSON-based configuration file, like so:

```json
{
  "team": "99999",
  "servers": [
    "192.168.1.1"
  ]
}
```

The parameters are as follows:

 * `team`: Your team id, used to display the leaderboard. You can find this in your Folding@Home client.

 * `servers`: This is a list of IP addresses of servers running the Folding@Home client. Using hostname may work but is not recommended.
