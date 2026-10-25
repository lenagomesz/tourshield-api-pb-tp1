"""Local administrative CLI; no public registration route."""
import argparse
import getpass
import re
from sqlalchemy.exc import IntegrityError
from app.config import get_secret
from app.database import add_user, initialize
from app.security import password_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,64}", args.username):
        parser.error("Usuário: 3-64 caracteres (letras, números, _, . ou -)")
    get_secret()
    password = getpass.getpass("Senha (mínimo 12 caracteres): ")
    if len(password) < 12 or len(password) > 1024:
        parser.error("Senha deve ter 12-1024 caracteres")
    if password != getpass.getpass("Confirme a senha: "):
        parser.error("Senhas diferentes")
    initialize()
    try:
        add_user(args.username, password_hash.hash(password))
    except IntegrityError:
        parser.error("Usuário já existe")
    print("Usuário criado; senha armazenada somente como hash Argon2.")


if __name__ == "__main__":
    main()
