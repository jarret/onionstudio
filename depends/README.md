Other Software
---------------

This is a slightly modified verion of the ZeroMQ plugin [cl-zmq.py](https://github.com/lightningd/plugins/pull/70). For running an onion studio server, it needs to be run with c-lightning and configured to publish `forward_event` and `htlc_accepted` notifications to a ZeroMQ endpoint such that the `onionstudio.py` server can read.

`example-subscriber.py` is also a slightly modified version of the example provided with the plugin to subscribe. Allows monitoring the `forward_event` and `htlc_accepted` events which might be helpful for development/debugging the server.
