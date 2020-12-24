from pydantic import BaseSettings


class Settings(BaseSettings):
    sqlalchemy_database_name: str = "sqlite:///./luckyGame.db"
    version_game_id:int = 1
    default_card_set: str= "x,x,x,x,x,x,x,x,x,x,x,x"

settings = Settings()
