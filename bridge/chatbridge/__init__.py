"""chatbridge -- a chat-app front door to a Claude Code session on a repository.

Telegram is the first adapter. Every instruction that arrives this way is
limited to the repository's CONTENT, whoever sends it, and every reply is a
few sentences with a link to the full answer. The design and its reasons are
in ../README.md; what a person has to do to run it is in ../SETUP.md.
"""

__version__ = "0.1.0"
