Репозиторий для работы по проекту ТППО.\
Чтобы удобнее работать с репозиторием (не через консоль) можно скачать приложение [GitHub desktop](https://desktop.github.com/download/).
## Основные команды  
1. **git status** – проверка статуса репозитория, показывает изменения в файлах, которые еще не закоммичены.
   ```
   git status
   ```  
2. **git log** – просмотр истории коммитов с их хешами и описаниями.
   ```
   git log
   ```  
3. **git clone "ссылка_на_репозиторий"** – клонирование удалённого репозитория на локальный компьютер.
   ```
   git clone https://github.com/user/repository.git
   ```  
4. **git init** – инициализация нового локального репозитория.
   ```
   git init
   ```  
5. **git add "имя_файла"** – добавление конкретного файла в индекс перед созданием коммита.
   ```
   git add file.txt
   или
   git add *.c (все файлы с расширением .c)
   ```  
6. **git add .** – добавление всех изменённых файлов в индекс.
   ```
   git add .
   ```  
7. **git commit -m "описание_коммита"** – фиксация изменений с сообщением.
   ```
   git commit -m "Добавлено новое описание"
   ```  
8. **git diff** – просмотр различий между текущими и предыдущими версиями файлов.
   ```
   git diff
   ```  
9. **git branch "имя_ветки"** – создание новой ветки в репозитории.
   ```
   git branch feature-branch
   ```  
10. **git checkout "имя_ветки"** – переключение на указанную ветку.
     ```
     git checkout feature-branch
     ```  
11. **git switch "имя_ветки"** – альтернативная команда для смены ветки в новых версиях Git.
    ```
    git switch feature-branch
    ```  
12. **git merge "имя_ветки"** – слияние указанной ветки с текущей.
    ```
    git merge feature-branch
    ```
13. **git push origin "имя_ветки"** – отправка локальных изменений указанной ветки в удалённый репозиторий.
    ```
    git push origin feature-branch
    ```  
14. **git pull origin "имя_ветки"** – получение и объединение изменений из удалённого репозитория в текущую ветку.
    ```
    git pull origin main
    ```  
15. **git fetch** – загрузка изменений с удалённого репозитория без их автоматического применения.
    ```
    git fetch
    ```  
16. **git branch -d "имя_ветки"** – удаление указанной локальной ветки.
    ```
    git branch -d feature-branch
    ```  
17. **git push origin --delete "имя_ветки"** – удаление указанной ветки в удалённом репозитории.
    ```
    git push origin --delete feature-branch
    ```  
18. **git reset --soft HEAD~1** – отмена последнего коммита, сохраняя изменения в файлах.
    ```
    git reset --soft HEAD~1
    ```  
19. **git reset --hard HEAD~1** – отмена последнего коммита с удалением изменений.
    ```
    git reset --hard HEAD~1
    ```  
20. **git submodule update --init --recursive** – обновление подмодулей в проекте.
    ```
    git submodule update --init --recursive
    ```  
21. **git config --global user.name "Ваше_Имя"** – настройка имени для коммитов.
    ```
    git config --global user.name "John Doe"
    ```  
22. **git config --global user.email "email@example.com"** – настройка email для коммитов.
    ```
    git config --global user.email "johndoe@example.com"
    ```
