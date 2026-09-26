"""Send welcome e-mails (here: return the message instead of sending it)."""

from users import UserStore


def send_welcome(store: UserStore, user_id: int) -> str:
    user = store.find_user(user_id)
    return f"To: {user.email}\nSubject: Welcome, {user.name}!"
