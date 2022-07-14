## Reserve

FastAPI + WebSocket + SSE server with external Triton gRPC service using Riva ASR

### About

This is a simple FastAPI + WebSocket + SSE implementation based on the Riva examples.
It uses gRPC to interface with Triton.  The audio data for a session is passed
in chunk-by-chunk via WebSockets and this is fed into a request queue.  The streaming ASR
task pulls data out of this queue and feeds it to the gRPC serve, and then
pushes the Transcripts onto a separate queue, which is then published via SSE 

### Installation

To get started with Riva, the quickstart is recommended:

https://catalog.ngc.nvidia.com/orgs/nvidia/teams/riva/resources/riva_quickstart

There is documentation on this process here:

https://docs.nvidia.com/deeplearning/riva/user-guide/docs/quick-start-guide.html#local-deployment-using-quick-start-scripts

#### About the Dockerfile and requirements.txt

The `riva_api` requirement is not available from the public PyPI.  It can be retrieved using the Riva quickstart process mentioned above.  This means that the requirements.txt will not work out of the box.  You can either install `riva_api` first locally, or if you have a private PyPI repository, you can push the wheel file to there and add it to your `pip.conf`.  That would look something like this:

```
no-cache-dir = true
index-url = https://pypi.org/simple
extra-index-url =
               http://{{EXTRA_HOST}}:{{EXTRA_HOST_PORT}}/nexus/repository/pypi-all/simple
trusted-host =
               {{EXTRA_HOST}}

```

After that, the `requirements.txt` should work for you.

If you dont want to mess up an existing `pip.conf`, you can use the `PIP_CONFIG_FILE` environment variable to refer to your own, which is what I have done in the `Dockerfile`.  The `Dockerfile` in this repository assumes that there is a `pip.conf` in the root directory, so you can make it run by copying the example above and replacing `{{EXTRA_HOST}}` and `{{EXTRA_PORT}}` with your private pypi.

#### RMIR and Triton Serving details

TODO.  For now, please refer to the Riva quickstart link mentioned in the previous section.


