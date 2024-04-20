# PyFahViewer - A Folding@Home Wall Display

This application serves as a wall display for viewing your Folding@Home team ranking and work unit progress.

![Demo screenshot](demoscreenshot.png)


## Requirements

 * Docker, OR Python 3.8+ with `virtualenv` (`pip install virtualenv`)
 * FAHClient version 7.4+


## Getting Started

1. Copy `config.example.json` to `config.json` and input your configuration parameters. See the _Configuration_ section for details.

2. From the Folding@Home client, go to Configure > Remote Access.

   1. Configure a password if desired.
   2. Under **IP Address Restriction** follow the instructions to configure a subnet that will allow the server running this application to reach the client.
   3. If you chose not to use a password, also configure this subnet under **Passwordless IP Address Restriction**.
   4. You may need to close the advanced control and restart Folding@Home for the changes to take effect.

3. Follow the instructions under _Running the Application_.


## Configuration

The application uses a JSON-based configuration file, like so:

```json
{
  "team": "1",
  "servers": [
    {"address": "192.168.1.10", "password": "abcd1234"},
    {"address": "192.168.1.11"}
  ]
}

```

The parameters are as follows:

 * `team`: Your team id, used to display the leaderboard. You can find this in your Folding@Home client. If this option is omitted, the leaderboard will not display.

 * `servers`: This is a list of servers running the Folding@Home client, formatted as a dictionary with the following options:

   * `address`: The IP address or hostname of the server. Note that using hostname may slow down fetches.

   * `password`: The password configured on the server. Omit this option if the server does not use a password. Authentication is also skipped if the password is null or the empty string.


## Running the Application

### Running in Docker (recommended)

From the project directory, run:

```bash
# If you want application output, you may wish to remove the -d flag.
docker-compose up -d
```

Docker will build the container with the appropriate dependencies and launch gunicorn to host the application. By
detault, the app runs on port 5000 and listens on all interfaces (`0.0.0.0`). You can change this on the `CMD` line of
`Dockerfile`.

If you desire to host the dashboard publicly, you may choose to use `nginx.sample.conf` (or your own configuration)
to put an nginx proxy in front of the app.

When you want to terminate the application, run the following from the project directory:

```bash
docker-compose down
```

### Running Without a Container

1. Install dependencies and set up the virtual environment:
   ```bash
   # First run
   virtualenv venv

   # Every run
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start the application while inside the virtualenv:
   ```bash
   gunicorn -b 0.0.0.0:5001 -w 1 wsgi:app
   ```

3. Navigate to `http://<server ip>:5001` in your browser.

4. When you're finished, you can press Ctrl+C in the terminal to stop the server, then run `deactivate` to return to your normal shell.


## Contributing
Contributions are welcome! If you see a problem or would like a feature, create an issue or open a pull request on this repository.


## License
This application is distributed with the MIT license. See the LICENSE file for more information.
