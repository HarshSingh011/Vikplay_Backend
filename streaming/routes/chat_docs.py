"""
chat_docs.py — WebSocket Chat Documentation Endpoints

Swagger/OpenAPI cannot natively document WebSocket endpoints, so these
HTTP GET endpoints act as documentation placeholders under the "chat (WebSocket)"
tag. They explain how to connect, what to send, and what to expect.
"""
from fastapi import APIRouter
from ..schemas.streaming_schemas import (
    WsChatSendSchema,
    WsChatReceiveSchema,
    WsBroadcasterConnectResponse,
    WsViewerConnectResponse,
)

router = APIRouter(
    prefix="/api/streaming/chat",
    tags=["chat (WebSocket)"],
)


@router.get(
    "/broadcaster/connect/{stream_code}",
    response_model=WsBroadcasterConnectResponse,
    summary="📡 Broadcaster — WebSocket Connection Guide",
)
async def broadcaster_ws_connect_guide(stream_code: str):
    """
    ## How the Broadcaster Connects & Sends Chat

    > ⚠️ This is a **documentation endpoint only**.
    > The real connection is a **WebSocket**, not HTTP.

    ---

    ### Step 1 — Get a token
    ```
    POST /auth/login
    Body: { "email": "you@example.com", "password": "..." }
    Response: { "access_token": "eyJ..." }
    ```

    ### Step 2 — Start the stream
    ```
    POST /api/streaming/streams/start
    Header: Authorization: Bearer <access_token>
    Body: { "title": "My Stream", "description": "...", "thumbnail_url": "..." }
    Response: { "stream_code": "A1B2C3", ... }
    ```

    ### Step 3 — Open broadcaster WebSocket
    ```
    ws://HOST/api/webrtc/ws/broadcast/{stream_code}?token=<access_token>
    ```
    (use `wss://` in production)

    ### Step 4 — Send a chat message (JSON over WS)
    ```json
    { "type": "chat_message", "username": "Alice", "message": "Hello viewers!" }
    ```

    ### All message types you can SEND:
    | type | purpose |
    |------|---------|
    | `chat_message` | Send a live chat message to all viewers |
    | `answer` | WebRTC SDP answer to a viewer's offer |
    | `ice_candidate` | WebRTC ICE candidate |
    | `sync_timestamp` | Sync playback: `{"type":"sync_timestamp","broadcaster_ts":12345}` |
    | `ping` | Keep-alive; server replies `{"type":"pong"}` |

    ### Messages you RECEIVE:
    | type | meaning |
    |------|---------|
    | `chat_message` | Chat sent by a viewer |
    | `offer` | WebRTC SDP offer from a viewer joining |
    | `ice_candidate` | WebRTC ICE candidate from a viewer |
    | `pong` | Response to your ping |

    ### On disconnect
    - Server records peak viewer count and marks stream as ended in DB.
    """
    return WsBroadcasterConnectResponse(
        ws_endpoint=f"ws://HOST/api/webrtc/ws/broadcast/{stream_code}?token=YOUR_TOKEN",
        token_required=True,
        query_params={"token": "required — JWT access_token from POST /auth/login"},
        send_message_types=["chat_message", "answer", "ice_candidate", "sync_timestamp", "ping"],
        receive_message_types=["chat_message", "offer", "ice_candidate", "pong"],
        example_chat_payload={"type": "chat_message", "username": "Alice", "message": "Hello viewers!"},
    )


@router.get(
    "/viewer/connect/{stream_code}",
    response_model=WsViewerConnectResponse,
    summary="📺 Viewer — WebSocket Connection Guide",
)
async def viewer_ws_connect_guide(stream_code: str):
    """
    ## How the Viewer Connects & Sends Chat

    > ⚠️ This is a **documentation endpoint only**.
    > The real connection is a **WebSocket**, not HTTP.

    ---

    ### Step 1 — Discover live streams
    ```
    GET /api/streaming/streams/live
    Response: [ { "stream_code": "A1B2C3", "title": "...", ... }, ... ]
    ```

    ### Step 2 — Load chat history (optional but recommended)
    ```
    GET /api/streaming/streams/code/{stream_code}/chat?limit=50
    Response: [ { "username": "Alice", "message": "...", "created_at": "..." }, ... ]
    ```

    ### Step 3 — Open viewer WebSocket
    ```
    ws://HOST/api/webrtc/ws/view/{stream_code}
    ws://HOST/api/webrtc/ws/view/{stream_code}?token=<access_token>   ← if logged in
    ```
    (use `wss://` in production)

    ### Step 4 — Send a chat message (JSON over WS)
    ```json
    { "type": "chat_message", "username": "Bob", "message": "Nice stream!" }
    ```

    ### All message types you can SEND:
    | type | purpose |
    |------|---------|
    | `chat_message` | Send a live chat message to broadcaster + all viewers |
    | `offer` | WebRTC SDP offer to start video connection |
    | `ice_candidate` | WebRTC ICE candidate |
    | `request_go_live` | Request to become a co-broadcaster |
    | `ping` | Keep-alive; server replies `{"type":"pong"}` |

    ### Messages you RECEIVE:
    | type | meaning |
    |------|---------|
    | `chat_message` | Chat from broadcaster or other viewers |
    | `answer` | WebRTC SDP answer from broadcaster |
    | `ice_candidate` | WebRTC ICE candidate from broadcaster |
    | `pong` | Response to your ping |
    | `error` | e.g. if you try to view your own stream |

    ### Notes
    - Token is **optional** — anonymous viewers are supported.
    - A viewer **cannot** join their own stream (server closes the WS with code 4006).
    """
    return WsViewerConnectResponse(
        ws_endpoint=f"ws://HOST/api/webrtc/ws/view/{stream_code}",
        token_required=False,
        query_params={"token": "optional — include your JWT to be identified as a registered user"},
        send_message_types=["chat_message", "offer", "ice_candidate", "request_go_live", "ping"],
        receive_message_types=["chat_message", "answer", "ice_candidate", "pong", "error"],
        example_chat_payload={"type": "chat_message", "username": "Bob", "message": "Nice stream!"},
    )


@router.get(
    "/message-format/send",
    response_model=WsChatSendSchema,
    summary="💬 WS Message Format — Sending a Chat Message",
)
async def ws_send_format():
    """
    ## JSON format for sending a chat message over WebSocket

    Both **broadcaster** and **viewer** use the exact same payload:

    ```json
    {
      "type": "chat_message",
      "username": "Alice",
      "message": "Hello everyone!"
    }
    ```

    | field | type | required | description |
    |-------|------|----------|-------------|
    | `type` | string | ✅ | Always `"chat_message"` |
    | `username` | string | ✅ | Display name shown in chat |
    | `message` | string | ✅ | Chat text content |

    **JavaScript example:**
    ```javascript
    ws.send(JSON.stringify({
      type: "chat_message",
      username: "Alice",
      message: "Hello everyone!"
    }));
    ```
    """
    return WsChatSendSchema(
        type="chat_message",
        username="Alice",
        message="Hello everyone!",
    )


@router.get(
    "/message-format/receive",
    response_model=WsChatReceiveSchema,
    summary="📨 WS Message Format — Receiving a Chat Message",
)
async def ws_receive_format():
    """
    ## JSON format received over WebSocket for an incoming chat message

    When a user sends a chat message, **everyone in the stream** receives:

    ```json
    {
      "type": "chat_message",
      "username": "Bob",
      "message": "Nice stream!",
      "role": "viewer"
    }
    ```

    | field | type | values | description |
    |-------|------|--------|-------------|
    | `type` | string | `"chat_message"` | Message type identifier |
    | `username` | string | any | Sender's display name |
    | `message` | string | any | Chat text |
    | `role` | string | `"broadcaster"` or `"viewer"` | Who sent the message |

    **JavaScript example (listening for chat):**
    ```javascript
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "chat_message") {
        console.log(`[${msg.role}] ${msg.username}: ${msg.message}`);
        // add to your chat UI
      }
    };
    ```
    """
    return WsChatReceiveSchema(
        type="chat_message",
        username="Bob",
        message="Nice stream!",
        role="viewer",
    )
