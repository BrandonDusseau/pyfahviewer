# PyFahViewer - A Folding@Home Wall Display

This application serves as a wall display for viewing your Folding@Home team ranking and work unit progress.

## Requirements

 * Python 3.x
 * `pipenv` (`pip install pipenv`)

## Getting Started

 1. Copy `config.example.json` to `config.json` and input your configuration parameters. See the _Configuration_ section for details.
 2. Install dependencies:
    ```bash
    cd pyfahviewer
    pipenv install
    ```
 3. Set up your Folding@Home clients to allow access from any IP.

  **NOTE:** You should not do this if your Folding@Home port is exposed to the internet. This project does not support password authentication at this time.

  1. From the Folding@Home client, go to Configure > Remote Access.

  2. Under **Passwordless IP Address Restriction** set value `0.0.0.0/0` and **Save**.

 4. Start the application:
    ```bash
    pipenv run python main.py
    ```

 5. Navigate to `http://localhost:5000` in your browser.

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
