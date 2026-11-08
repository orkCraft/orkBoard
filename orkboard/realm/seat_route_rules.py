"""Orkmaster route rules shared by calls and agent frames. Existing providers re-export their original names."""


def rules() -> str:
    """The route's rules (spec 154 A.1): what the Orkmaster judges and how, apart from the call's frame. `instruction` and an agent's frame (`seat_frames.agent("orkmaster", "route")`) both hold this text."""
    return """A person wrote a goal for their project. Say which of the project's parties work on it, in the order they should \
be heard: the party that makes the product, then the one that makes its look, then the one that writes its code, then the one that runs it, then the one \
that markets it. Name only the parties the goal needs; never invent one."""

