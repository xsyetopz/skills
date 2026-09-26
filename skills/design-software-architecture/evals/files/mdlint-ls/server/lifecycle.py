"""Handles the LSP `initialize` request."""


def initialize(params: dict) -> dict:
    return {
        "capabilities": {"textDocumentSync": 1},
        "serverInfo": {"name": "mdlint-ls", "version": "0.4.0"},
    }
