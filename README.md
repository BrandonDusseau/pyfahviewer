# PyFahViewer - A Folding@Home Wall Display

This application serves as a wall display for viewing your Folding@Home team ranking and work unit progress.

![Demo screenshot](demoscreenshot.png)


## Requirements

 * Docker, OR Python 3.9+ with `venv` (`python3 -m pip install venv`)
 * FAHClient version 7.4+ or 8.1+


## Getting Started

To get started follow the instructions in each of the below sections.


### 1. Configuring the Folding@Home Client

You'll need to configure Folding@Home to allow remote connections. This differs based on the client version you're using.


#### v8 Client (Bastet)

Take a look at [this forum post](https://foldingforum.org/viewtopic.php?p=358836&sid=eefce116908aa2f2ef3e0cb5069f0598#p358836)
to learn how to configure your client for remote access. Note that the v8 client does not support password
authentication like the v7 client did, so be sure not to open your client port to the public.

The location of the configuration file depends on your platform:

 * **macOS**: `/Library/Application Support/FAHClient/config.xml`
 * **Linux**: `/etc/fah-client/config.xml`
 * **macOS**: `C:\ProgramData\FAHClient\config.xml`


#### v7 Client (Bastet)

From the Folding@Home client, go to Configure > Remote Access.

   1. Configure a password if desired.
   2. Under **IP Address Restriction** follow the instructions to configure a subnet that will allow the server running this application to reach the client.
   3. If you chose not to use a password, also configure this subnet under **Passwordless IP Address Restriction**.
   4. You may need to close the advanced control and restart Folding@Home for the changes to take effect.


### 2. Configuring pyFahViewer

Copy `config.example.json` to `config.json`, then use the information below to configure pyFahViewer.

The application uses a JSON-based configuration file, like so:

```json
{
  "team": "1",
  "servers": [
    {"address": "192.168.1.10", "password": "abcd1234", "clientVersion": "7"},
    {"address": "192.168.1.11", "port": "7396", "clientVersion": "8"}
  ]
}

```

The parameters are as follows:

 * `team`: Your team id, used to display the leaderboard. You can find this in your Folding@Home client. If this option is omitted, the leaderboard will not display.

 * `servers`: This is a list of servers running the Folding@Home client, formatted as a dictionary with the following options. If this section is omitted, the work progress will not be displayed.

   * `address` (required): The IP address or hostname of the server. Note that using hostname may slow down fetches.

   * `port`: The port the Folding@Home client is listening on. For client v7 this has no effect. For client v8, the value will default to `7396` if not specified.

   * `client` (required): The Folding@Home client version. Accepted values are `7` and `8`.

   * `password`: The password configured on the server. Omit this option if the server does not use a password. Authentication is also skipped if the password is null or the empty string. This has no effect on v8 clients.


### Running the Application

#### Running in Docker (recommended)

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


#### Running Without a Container

1. Install dependencies and set up the virtual environment:
   ```bash
   # First run
   python3 -m venv env

   # Every run
   source env/bin/activate
   python3 -m pip install -r requirements.txt
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
