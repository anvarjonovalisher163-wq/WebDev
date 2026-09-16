from cryptography.fernet import Fernet, InvalidToken


class CryptoService:
    """Guruhning Gemini API kalitini saqlash vaqtida shifrlash/deshifrlash."""

    def __init__(self, secret: str) -> None:
        self._fernet = Fernet(secret.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, token: str) -> str | None:
        try:
            return self._fernet.decrypt(token.encode()).decode()
        except InvalidToken:
            return None
