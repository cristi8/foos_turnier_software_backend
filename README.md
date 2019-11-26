# foos_turnier_software_backend

Software website: https://www.dtfb.de/index.php/tifu-die-software

## Info

This repo aims to provide an alternative backend to the software, making it easy to use in unofficial setups and gather tournament results in a database.


When uploading results, the software can be set up to send the results to a specific backend URL.

After reverse-engineering the communication between the software and the backend, this repo aims to be an alternative backend.


`poc.py` is a proof of concept that simulates login and receives the tournament results and stores them in mongodb.
It also has a /view endpoint that displays tournaments from the database
