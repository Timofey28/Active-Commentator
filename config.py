import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    target_group_id: int
    user_token: str
    last_post_id_file: str
    openai_api_key: str

    hostname: str
    username: str = Field(alias='USER_NAME')  # дичь ебаная блять 20 минут убил на это
    password: str
    private_key_path: str

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), ".env")


settings = Settings()
if not os.path.exists(settings.last_post_id_file):
    with open(settings.last_post_id_file, "w") as file:
        file.write("0")