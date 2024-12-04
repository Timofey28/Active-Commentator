import logging
import os
from logging.handlers import RotatingFileHandler

import vk_api
from apscheduler.schedulers.blocking import BlockingScheduler
from openai import OpenAI

from config import settings


def get_last_post_info() -> dict:
    response = vk.wall.get(owner_id=-settings.target_group_id, count=2, filter='owner')
    items = response["items"]
    if 'is_pinned' in items[0] and items[0]['is_pinned'] == 1:
        item = items[1]
    else:
        item = items[0]
    return {
        "id": item["id"],
        "text": item["text"]
    }


def post_is_new(post_info: dict) -> bool:
    if not os.path.exists(settings.last_post_id_file):
        with open(settings.last_post_id_file, "w") as file:
            file.write(str(post_info["id"]))
        return False
    with open(settings.last_post_id_file) as file:
        last_post_id = int(file.read())
    if last_post_id == post_info["id"]:
        return False
    with open(settings.last_post_id_file, "w") as file:
        file.write(str(post_info["id"]))
    return True


def generate_comment(post_text: str) -> str:
    prompt = "Есть сообщество Вконтакте, посвященное соляной пещере и оказывающее услуги оздоровительного характера: "
    prompt += "сеансы галотерапии, массаж в профессиональном массажном кресле премиум-класса и фитобочка. Сгенерируй "
    prompt += "небольшой позитивный комментарий к последнему посту сообщества, который мог бы оставить активный "
    prompt += "пользователь и участник данного сообщества мужского рода. В комментарии не пиши ссылки на других "
    prompt += "пользователей и не упоминай их напрямую. Комментарий должен подходить по смыслу к посту, текст которого "
    prompt += "представлен далее:\n\n"
    prompt += post_text

    response = openai.chat.completions.create(
        model="gpt-4o",
        temperature=1.0,
        top_p=0.9,
        messages=[
            {"role": "system", "content": "You are a helpful assistant which generates positive and meaningful comments to posts in social network."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content.strip()


def check_for_new_posts():
    post = get_last_post_info()
    if post_is_new(post):
        logger.info(f'New post detected: {post["id"]}')
        comment = generate_comment(post["text"])
        logger.info('Comment generated ))')
        vk.likes.add(type='post', owner_id=-settings.target_group_id, item_id=post["id"])
        logger.info('Post liked')
        vk.wall.createComment(owner_id=-settings.target_group_id, post_id=post["id"], message=comment)
        logger.info(f'Comment posted on https://vk.com/club{settings.target_group_id}?w=wall-{settings.target_group_id}_{post["id"]}:\n{comment}\n')


if __name__ == '__main__':
    open('info.log', 'w').close()
    handler = RotatingFileHandler(
        filename='info.log',
        mode='w',
        maxBytes=1_000_000,
        backupCount=1,
        encoding='utf-8',
    )
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger('httpx')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.info('Started logging...')

    session = vk_api.VkApi(token=settings.user_token)
    vk = session.get_api()
    openai = OpenAI(api_key=settings.openai_api_key)

    scheduler = BlockingScheduler()
    scheduler.add_job(check_for_new_posts, 'interval', seconds=60)
    print('Running...')
    scheduler.start()
