import os

from adapters.card_gateway import CardGateway


def build_gateway():
    return CardGateway(os.environ["CARD_API_URL"], os.environ["CARD_API_KEY"])
