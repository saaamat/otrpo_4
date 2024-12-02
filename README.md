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
      #Запуск с параметризацией в консоли(пример)
      '''
      --uri - URI к бд Neo4j
      --user - пользователь
      --password - пароль пользователя
      Для вывода результата запросов
      
      --top_users N - топ N пользователей по кол-ву подписчиков
      --top_groups N - топ N групп по кол-ву подписчиков
      --fetch_users - количество пользователей
      --fetch_groups - количество групп
      --fetch_followed_users - количество пользователей-подписчиков
      '''
      python main.py --uri "bolt://localhost:7687" --user "neo4j" --password "password" --top_users 5 --top_groups 5 --fetch_users --fetch_groups --fetch_followed_users
