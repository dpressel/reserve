import logging
import json
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from asr import ASRPipe
from session import SessionManager
from starlette.responses import StreamingResponse
import socketio

logging.basicConfig(format="%(asctime)s : %(message)s", level=logging.DEBUG)


config = {}
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["OPTIONS"],
    allow_headers=["Origin", "X-Requested-With"],
)


sio = socketio.AsyncServer(
    async_mode="asgi", cors_allowed_origins="*", logger=False, engineio_logger=False
)


@app.on_event("startup")
async def startup_event():
    pass


@app.get("/health")
async def health_check():
    return {"status": "OK"}


@app.post("/init")
async def init_state(bg: BackgroundTasks):
    session = SessionManager.create_session(ASRPipe())
    bg.add_task(session.asr.main_asr)
    return {"key": session.key}


@app.get("/stream")
def stream(key: str):
    """This sets up an HTTP SSE connection which is a one-way push from server to client

    The client will call with an HTTP request and the connection is kept open and whenever a transcript
    is found, it is sent over the socket.

    :param key: The session_id is used to get a stream that is specific to a session
    :return: a streaming response
    """
    session = SessionManager.get_session(key)

    def event_generator():
        yield "\n"
        for next_msg in session.get_asr_transcript():
            yield "data:" + json.dumps(
                {"event": "audio.tx", "key": key, "transcript": next_msg}
            ) + "\n\n"

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }
    return StreamingResponse(
        event_generator(), media_type="text/event-stream", headers=headers
    )


# FIXME:  should only need one of these, here we are adding the app from ASGIApp, then we are mounting
socket_app = socketio.ASGIApp(sio, app, socketio_path="/ws")
app.mount("/ws", socket_app)


@sio.on("audio_in")
def receive_remote_audio(sid, data):
    """Audio chunks are sent from the client to the server via this message, and the data is placed in the input buffer

    :param sid: socketio sid
    :param data: dict containing the user_id and the data content
    :return:
    """
    logging.debug(f"[{sid}] Filling ASR buffer")
    SessionManager.get_session(data["key"]).fill_asr_buffer(data["data"])


@sio.on("connect")
def connect(sid, _):
    """This method is called when the socketio is connected

    :param sid: The socketio sid
    :param _: unused
    :return:
    """
    logging.info(f"[{sid}] Client connected")


@sio.on("disconnect")
def disconnect(sid):
    """This method is called when the socketio is disconnected

    :param sid: The socketio sid
    :return:
    """
    logging.info(f"[{sid}] Client disconnected")
