## 1. В файле .env указать свои данные 
    VK_TOKEN=''
    USER_ID=''
    NEO_URI=''
    NEO_USER=''
    NEO_PASSWORD=''
## 2. Для запуска перейти к директории проекта через cd
    cd ./otrpo_4

## 3. Установите все зависимости 
    pip install -r requirements.txt
## 4. Запуск программы
      python main.py 
## 5. Запросы
 - Все пользователи
``` 
  MATCH (u:User) 
  RETURN u.id AS id, u.name AS name,
  u.sex AS sex, u.home_town AS home_town 
```
- Все группы
``` 
  MATCH (g:Group) 
  RETURN g.id AS id, g.name AS name,
  g.screen_name AS screen_name
```
- Топ 5 пользователей по кол-ву подписчиков
``` 
  MATCH (u:User)-[:FOLLOW]->(f:User)
        WITH u, count(f) AS followers_count
        ORDER BY followers_count DESC
        LIMIT 5
        RETURN u.id AS id, u.name AS name, followers_count
```
- Топ 5 групп по кол-ву подписчиков(объекты User)
``` 
   MATCH (g:Group)<-[:SUBSCRIBE]-(u:User)
        WITH g, count(u) AS subscribers_count
        ORDER BY subscribers_count DESC
        LIMIT 5
        RETURN g.id AS id, g.name AS name, subscribers_count
```
- Пользователи, которые подписчики друг другу
``` 
   MATCH (u1:User)-[:FOLLOW]->(u2:User)-[:FOLLOW]->(u1:User)
   RETURN u1.id AS id1, u1.name AS name1, u2.id AS id2, u2.name AS name2
```
