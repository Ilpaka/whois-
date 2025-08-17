from __future__ import annotations
from fastapi import Depends, Request

def get_ws_manager(request: Request):
    return request.app.state.ws_manager
