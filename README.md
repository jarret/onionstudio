![Onion Studo Logo](frontend/htdocs/img/logo.png "Onion Studio Logo")

# Onion Studio!

An application of TLV extension data in onion packets for drawing anonymous art via the Lightning Network.

https://onion.studio


# Drawing Pixels

## Dependencies
This requires you be running [C-Lightning](https://github.com/ElementsProject/lightning) version `v0.8.0` or later. The provided client uses the `createonion` and `sendonion` RPC calls introduced in `v0.8.0`. At this time, I am aware of no other LN wallet or node implementation that supports building onion packets to include Onion Studio's custom TLV extensions.

The provided client also uses the Python wrapper that is imported as `pyln.client` which is installed the PyPi package `pyln-client` (formerly `pylightning`).

```
$ sudo pip3 install pyln-client
```

In order for the client to be able to interpret .png files as source images, it requires the `pillow` image processing library for Python package to be installed. This has additional package dependencies which may vary by system. For Ubuntu/Debian:
```
$ sudo apt-get install libopenjp2-7 libtiff5
$ sudo pip3 install pillow
```

## Cloning this repo

You will need the client scripts provided. You can get them by cloning this repository:
```
$ git clone https://github.com/jarret/onionstudio
$ cd onionstudio
```

## Pixel Coordinates and Colors

On [the frontend of Onion Studio](https://onion.studio), the drawable pixel grid is 1024 pixels by 1024 pixels. The top left corner pixel is coordinate `(0, 0)`. The bottom right pixel is coordinate `(1023, 1023)`. When drawing from .png source files, the placement coordinate you will need to specify is where to align the top left corner of that image on this grid.

The 'native' color depth of this art space is 12 bit colors which are specified by 3-character hex RGB strings. Eg.


| 12-bit hex    | Color          |
| ------------- |:--------------:|
| 000           | Black          |
| f00           | Red            |
| 0f0           | Green          |
| 00f           | Blue           |
| fff           | White          |


If you provide a .png file of a different color depth, the colors will be clamped to 12 bits of precision per pixel.

If you provide a .png file with alpha channel transparency, the transparent pixels will be dropped from the purchase, allowing you to cleanly place irregularly-shaped images on top of others.

## Pricing

Each pixel costs 1 satoshi to draw, which is inexpensive, unless you are drawing a large .png image, for which the costs can add up quickly. The scripts will require you to opt-in with the `--big` flag to draw more than 1000 pixels in one instruction. It is suggested that you test things out with small draws to validate your understanding before getting more ambitious.

## Drawing via Standalone Client

In this repository, the [onionstudio-draw.py](onionstudio-draw.py) executable will draw pixels via your provided input parameters. However, it will need to be pointed at the JSON-RPC file of your running C-Lightning node which is typically in your `lightning-dir`. You will also need to choose between `manual` and `png` mode for the style of drawing.

```
$ ./onionstudio-draw.py /path/to/lightining-dir/bitcoin/lightning-rpc manual -h
usage: onion-draw.py lightning_rpc manual [-h] pixels

positional arguments:
  pixels      a string specifying coordinates and colors of pixels to draw
              separated by underscores. Eg. 1_1_fff_2_2_0f0 will set pixel
              (1,1) white (#fff) and (2,2) green (#0f0)

optional arguments:
  -h, --help  show this help message and exit

$ ./onionstudio-draw.py ~/lightningd-run/lightning-dir/bitcoin/lightning-rpc png -h
usage: onion-draw.py lightning_rpc png [-h] [-b] x_offset y_offset png_file

positional arguments:
  x_offset    the x coordinate to begin drawing at
  y_offset    the y coordinate to begin drawing at
  png_file    the path to the png file to use

optional arguments:
  -h, --help  show this help message and exit
  -b, --big   acknowledge that this is a big spend and proceed anyway

```

As seen above the `-h` flag describes the options. For example, to draw a single black pixel at coordinate `(100, 100)`, you give the command:

```
$ ./onionstudio-draw.py /path/to/lightining-dir/bitcoin/lightning-rpc manual 100_100_000
```

To draw a .png file of your creation with the top-left corner placed at coordinate `(300, 400)`, you give the command.
```
$ ./onionstudio-draw.py /path/to/lightining-dir/bitcoin/lightning-rpc png 300 400 /path/to/my/image.png
```

## Drawing via Plugin

For convenience, the same functionality is also bundled into a C-Lightning plugin. The [onionstudio-draw-plugin.py](onionstudio-draw-plugin.py) is the plugin executable to be copied to the `plugin/` directory of your C-Lightning node. The `bolt/` and `onionstudio/` directories of this repo will need to be copied to the `plugin/` directory also.

```
$ cp -r onionstudio-draw-plugin.py bolt onionstudio /path/to/lightning-dir/plugins/
```

Upon loading this plugin, your `lightning-cli` interface should have the `os_draw_pixels` and `os_draw_png` commands. The equivalents of the earlier two examples are:

```
$ lightning-cli os_draw_pixels 100_100_000
```

```
$ lightning-cli os_draw_png 300 400 /path/to/my/image.png
```

If you have any trouble loading the plugin, please ensure the standalone script works first since it will give you easier-to-read error messages if there are any dependancy problems.


# Running My Own Onion Studio Server

## Running the ZeroMQ plugin

The provided [cl-zmq.py](depends/cl-zmq.py) plugin is a slightly modified version of [the one in the official community repo](https://github.com/lightningd/plugins/tree/master/zmq). It is needed to publish the `forward_event` notification and the `htlc_accepted` hook to a ZeroMQ endpoint where the Onion Studio Server can pick it up. This plugin will need to be loaded and the node will need to be started with launch args that are similar to: `--zmq-pub-forward-event=tcp://0.0.0.0:5556 --zmq-pub-htlc-accepted=tcp://0.0.0.0:5556` in order to configure the plugin to publish to that specific endpoint (`tcp://0.0.0.0:5556` in the example). The [example-subscriber.py](depends/example-subscriber.py) script might be useful for testing, observing, and logging these events as seen by the server.

## Running the Server

The [onionstudio.py](onionstudio.py) script is the websocket server and application logic. It will read events from the endpoint, accept valid payloads, update the stored image state and notify any connected websocket clients of the newly purchased pixels. This script has help output which describes the configuration options:
```
$ ./onionstudio.py -h
usage: onionstudio.py [-h] [-e ENDPOINT] [-m MOCK_ENDPOINT]
                      [-w WEBSOCKET_PORT] [-a ART_DB_DIR]

optional arguments:
  -h, --help            show this help message and exit
  -e ENDPOINT, --endpoint ENDPOINT
                        endpoint to subscribe to for zmq notifications from
                        c-lightning via cl-zmq.py plugin
  -m MOCK_ENDPOINT, --mock-endpoint MOCK_ENDPOINT
                        endpoint to subscribe to zmq notifcations from a test
                        script such as mock-png.py
  -w WEBSOCKET_PORT, --websocket-port WEBSOCKET_PORT
                        port to listen for incoming websocket connections
  -a ART_DB_DIR, --art-db-dir ART_DB_DIR
                        directory to save the image state and logs
```

## Running the frontend

The [frontend/](frontend/) directory has the html and javascript of the frontend web page. For running with your setup, it will need to be modified to connect to the right websocket host and port (ws://localhost:9000) for example.

## Testing with Art.

The server can be configured with the `MOCK_ENDPOINT` launch arg to accept payloads from that second endpoint. A [test script](test/mock-tlv-png.py) has been provided which can publish valid `htlc_accepted` and `forward_event` payloads with valid pixels to that endpoint based on an arbitrary .png. This may be useful for testing that everything works before relying on real LN payments to drive the app.


# Crash Course: How Do I Make My Own Extension TLV App?

At this time (Jan. 2020) everything here is very bleeding-edge and raw. This application's implementation may help guide you on how to do it with C-Lightning, but there will likely be better ways in the future. Here is a quick tour of what is here:

## Basic TLV Encoding
The code under [bolt/](bolt/) handles the encoding of TLVs and payloads according to the BOLT 1 and BOLT 4 specifications. In particular, [hop_payload.py](bolt/hop_payload.py) uses the rest of the utilities to encode and parse hop payloads for the onion packets that give normal TLV routing instructions as per BOLT 4.

## Creating Extension TLVs

The source file [extension.py](onionstudio/extension.py) takes the normal TLV payload with routing instructions and appends the encoded extension TLVs. The extension TLVs are encoded using the `bolt/` library's TLV class, but with the type value set to an odd number greater than 65536 as is valid for extension TLVs per the BOLT 4 spec.

## Creating Onion Packets

C-Lightning provides the `createonion` command, however there are a few things to watch out for. First, the onion packets must be 1300 bytes large, all the payloads encoding size and hop distances vary in size. As a result, finding a payload set that fits in under the onion packet's hard limit takes some trial-and-error iteration,  The source file [onion.py](onionstudio/onion.py) goes through the iteration of building a right-sized onion by varying the number of encoded pixels.

## Circular Routing

Onion Studio routes to pay the destination by routing in a circular path and paying the destination via the routing hop fee. That means that the BOLT11 invoice is created by your local node and paid by your same local node via the circular route (this is similar to how channel re-balances work). This avoids the problem of needing to coordinate with the destination node and/or doing some sort of "Key Send" operation to make a undirectional payment. Conceptually, this circular payment might be a bit to grok at first, but it is a powerful tool for app design that Onion Studio demonstrates.

## Receiving Extension TLVs

C-Lightning's plugin system allows an application to register for the `htlc_accepted` hook which allows you to examine the TLV payloads as they are being used to route. At this time, the application can parse the payload and examine the forwarding payment that will be made if this HTLC is fulfilled.


Similarly, an application can use the plugin system to register for the `forward_event` notification to know when a forwarding HTLC is fulfilled. If it matches the `payment_hash` value of the previous `htlc_accepted` hook notification, that means that the node has been paid and the extension TLV can be executed on.

Onion Studio demonstrates how these value can be obtained via a plugin and passed in and parsed by an app [onionstudio.py](onionstudio.py). However, the `forward_event` and `htlc_accepted` data gets passed to it via the [cl-zmq.py](depends/cl-zmq.py) plugin over ZeroMQ rather than have the websocket server directly connected to the plugin. It is suggested that this is a good architectural template to build apps of this type off of rather than put an access of application logic directly in a plugin script.

# What's With the Clown?

Science has proven that unmoderated anarchic artwork converges towards clown vomit.
