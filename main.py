import requests
from neo4j import GraphDatabase
from loguru import logger
import os
from dotenv import load_dotenv


logger.add("debug.log", level="DEBUG")

load_dotenv()

VK_API_TOKEN = os.getenv('VK_TOKEN')   # Ваш токен доступа
VK_API_VERSION = "5.131"  # Версия API
BASE_URL = "https://api.vk.com/method/"

# Настройки Neo4j
NEO4J_URI = os.getenv('NEO_URI')
NEO4J_USER = os.getenv('NEO_USER')
NEO4J_PASSWORD = os.getenv('NEO_PASSWORD')
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


class Neo4jDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def save_user(self, user):
        query = """
        MERGE (u:User {id: $id})
        SET u.screen_name = $screen_name, u.name = $name, u.sex = $sex, u.home_town = $home_town
        """
        with self.driver.session() as session:
            session.run(query, user)

    def save_group(self, group):
        query = """
        MERGE (g:Group {id: $id})
        SET g.name = $name, g.screen_name = $screen_name, g.count = $count
        """
        with self.driver.session() as session:
            session.run(query, group)

    def save_relationship(self, user_id, target_id):
        query = f"""
        MATCH (u:User {{id: $user_id}})
        MATCH (t:User {{id: $target_id}})
        MERGE (u)-[:FOLLOW]->(t)
        """
        with self.driver.session() as session:
            session.run(query, {"user_id": user_id, "target_id": target_id})

    def save_subscribe(self, user_id, target_id):
        query = f"""
        MATCH (u:User {{id: $user_id}})
        MATCH (g:Group {{id: $target_id}})
        MERGE (u)-[:SUBSCRIBE]->(g)
        """
        with self.driver.session() as session:
            session.run(query, {"user_id": user_id, "target_id": target_id})

    def get_all_users(self):
        query = "MATCH (u:User) RETURN u.id AS id, u.name AS name, u.screen_name AS screen_name, u.sex AS sex, u.home_town AS home_town"
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    def get_all_groups(self):
        query = "MATCH (g:Group) RETURN g.id AS id, g.name AS name, g.screen_name AS screen_name"
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    def get_top_users_by_followers(self, top_n=5):
        query = f"""
        MATCH (u:User)-[:FOLLOW]->(f:User)
        WITH u, count(f) AS followers_count
        ORDER BY followers_count DESC
        LIMIT {top_n}
        RETURN u.id AS id, u.name AS name, followers_count
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    def get_top_groups_by_popularity(self, top_n=5):
        query = f"""
        MATCH (g:Group)<-[:SUBSCRIBE]-(u:User)
        WITH g, count(u) AS subscribers_count
        ORDER BY subscribers_count DESC
        LIMIT {top_n}
        RETURN g.id AS id, g.name AS name, subscribers_count
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    def get_users_following_each_other(self):
        query = """
        MATCH (u1:User)-[:FOLLOW]->(u2:User)-[:FOLLOW]->(u1:User)
        RETURN u1.id AS id1, u1.name AS name1, u2.id AS id2, u2.name AS name2
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

def vk_request(method, params):
    params.update({"access_token": os.getenv('VK_TOKEN'), "v": '5.132'})
    try:
        response = requests.get(BASE_URL + method, params=params)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            logger.warning(f"VK API Error: {data['error']}")
            return None
        return data.get("response")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

# Сбор данных
def get_user_followers(user_id):
    followers = vk_request("users.getFollowers", {"user_id": user_id})
    return followers.get("items", []) if followers else []

def get_user_groups(user_id):
    groups = vk_request("groups.get", {"user_id": user_id, "extended": 1, "fields": "name,screen_name,members_count", "count": 100})
    return groups.get("items", []) if groups else []

def get_user_info(user_ids):
    users = vk_request("users.get", {"user_ids": ",".join(map(str, user_ids)), "fields": "sex,city,home_town"})
    return users if users else []

# Добавление данных в БД
def collect_data_recursive(user_id, db, current_depth, depth, processed_users=None, followers=None):
    """
    Рекурсивный сбор данных о пользователях и их связях.

    :param user_id: ID пользователя
    :param db: Экземпляр базы данных Neo4jDB
    :param depth: Максимальная глубина обхода
    :param current_depth: Текущая глубина рекурсии
    :param processed_users: Множество уже обработанных пользователей
    """
    if processed_users is None:
        processed_users = set()
    if current_depth > depth or user_id in processed_users:
        return

    processed_users.add(user_id)
    logger.info(f"Обрабатываем пользователя {user_id} на уровне {current_depth}")
    # Получение информации о пользователе
    user_info = get_user_info([user_id])
    if user_info:
        user = {
            "id": user_info[0].get('id', 0),
            "screen_name": user_info[0].get("screen_name", ""),
            "name": f"{user_info[0].get('first_name', '')} {user_info[0].get('last_name', '')}",
            "sex": user_info[0].get("sex", 0),
            "home_town": user_info[0].get("home_town", "")
        }
        logger.info(f'Добавляем пользователя {user['id']}')
        db.save_user(user)
        followers = get_user_followers(user_info[0].get('id'))

    foll = []
    if followers:
        for follower_id in followers:
            follower_info = get_user_info([follower_id])
            if follower_info:
                follower = {
                    "id": follower_info[0]["id"],
                    "screen_name": follower_info[0].get("screen_name", ""),
                    "name": f"{follower_info[0].get('first_name', '')} {follower_info[0].get('last_name', '')}",
                    "sex": follower_info[0].get("sex", 0),
                    "home_town": follower_info[0].get("home_town", "")
                }
                db.save_user(follower)
                db.save_relationship(user_id, follower['id'])
                foll.append(follower_id)



        processed_groups = set()  # Набор для хранения уникальных ID групп
        groups = get_user_groups(user_id)

        for group in groups:
            group_id = group["id"]
            if group_id not in processed_groups:  # Проверяем, была ли уже обработана группа
                group_data = {
                    "id": group_id,
                    "name": group.get("name", ""),
                    "screen_name": group.get("screen_name", ""),
                    "count": group.get("members_count", 0)
                }
                logger.info(f'Добавляем группу {group_data['id']}')
                db.save_group(group_data)  # Сохраняем только уникальные группы
                db.save_subscribe(user_id, group_id)
                processed_groups.add(group_id)  # Добавляем ID группы в набор

        for f in foll:
            collect_data_recursive(f, db, current_depth + 1, depth, processed_users)

if __name__ == "__main__":

    start_user_id = os.getenv('USER_ID')
    try:
        db = Neo4jDB(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        collect_data_recursive(start_user_id, db, current_depth=0, depth=2)

    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        db.close()
        logger.info("Завершено.")

        


