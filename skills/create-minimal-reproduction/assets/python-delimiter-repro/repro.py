"""Reproduce delimiter parsing failure for a payload containing the delimiter."""

message = "42|start|stop"
message_id, text = message.split("|")
print(message_id, text)
