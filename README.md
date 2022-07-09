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

