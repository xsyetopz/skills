import sys

from notes import add_note, list_notes

if __name__ == "__main__":
    user, text = sys.argv[1], sys.argv[2]
    add_note(usr=user, text=text)
    print("\n".join(list_notes(usr=user)))
