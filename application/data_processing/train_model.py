# train_model.py
from datasets import Dataset
from setfit import SetFitModel, SetFitTrainer
from enum import Enum
import os


class NewsCategory(Enum):
    CULTURE = "Культура"
    SPORT = "Спорт"
    TECHNOLOGY = "Технологии"
    HOLIDAYS = "Праздники"
    EDUCATION = "Образование"
    INCIDENTS = "Происшествия"
    SOCIETY = "Общество"
    OTHER = "Другое"


# Обучающая выборка
TRAIN_DATA = [
    # Культура
    ("в музее открылась новая выставка", NewsCategory.CULTURE.value),
    ("театр драмы представил премьеру", NewsCategory.CULTURE.value),
    ("ансамбль исполнил классические произведения", NewsCategory.CULTURE.value),
    ("фестиваль народной культуры прошёл в центре", NewsCategory.CULTURE.value),
    ("юные артистки стали лауреатами конкурса", NewsCategory.CULTURE.value),
    ("в библиотеке прошла встреча с писателем", NewsCategory.CULTURE.value),
    ("хореографический спектакль посвятили узницам концлагерей", NewsCategory.CULTURE.value),
    ("открытие нового театрального сезона", NewsCategory.CULTURE.value),
    ("прошёл концерт памяти военных лет", NewsCategory.CULTURE.value),
    ("детская школа искусств провела день открытых дверей", NewsCategory.CULTURE.value),
    ("кинофестиваль стартовал в Карелии", NewsCategory.CULTURE.value),
    ("реставрация мозаики Калевала обсуждается в Минкульте", NewsCategory.CULTURE.value),

    # Спорт
    ("соревнования по гимнастике состоялись в Петрозаводске", NewsCategory.SPORT.value),
    ("футболисты сыграли матч", NewsCategory.SPORT.value),
    ("байкеры открыли мотосезон", NewsCategory.SPORT.value),
    ("хоккейная команда победила", NewsCategory.SPORT.value),
    ("марафон прошёл в центре города", NewsCategory.SPORT.value),
    ("выпускницам спортшколы вручили награды", NewsCategory.SPORT.value),
    ("состоялся турнир по шахматам", NewsCategory.SPORT.value),
    ("сборная по лыжам отправилась на соревнования", NewsCategory.SPORT.value),
    ("в бассейне прошёл чемпионат по плаванию", NewsCategory.SPORT.value),
    ("теннисный корт в Ключевой снова открыт", NewsCategory.SPORT.value),
    ("прошли показательные выступления гимнасток", NewsCategory.SPORT.value),
    ("спортсмены из Карелии завоевали медали на первенстве", NewsCategory.SPORT.value),

    # Технологии
    ("внедрение VoWiFi в Карелии", NewsCategory.TECHNOLOGY.value),
    ("стартап получил финансирование", NewsCategory.TECHNOLOGY.value),
    ("абоненты Т2 могут звонить по WiFi", NewsCategory.TECHNOLOGY.value),
    ("мобильное приложение для жителей города", NewsCategory.TECHNOLOGY.value),
    ("в школе прошёл урок цифровой грамотности", NewsCategory.TECHNOLOGY.value),
    ("разработка голосового помощника", NewsCategory.TECHNOLOGY.value),
    ("в университете открыли лабораторию ИИ", NewsCategory.TECHNOLOGY.value),
    ("новые серверы установлены в дата-центре", NewsCategory.TECHNOLOGY.value),
    ("провайдер повысил скорость интернета", NewsCategory.TECHNOLOGY.value),
    ("прошёл митап айтишников", NewsCategory.TECHNOLOGY.value),
    ("запущен сайт для приёма обращений граждан", NewsCategory.TECHNOLOGY.value),
    ("появилось приложение по отслеживанию автобусов", NewsCategory.TECHNOLOGY.value),

    # Праздники
    ("1 мая – праздник Весны и Труда", NewsCategory.HOLIDAYS.value),
    ("масленица прошла на площади", NewsCategory.HOLIDAYS.value),
    ("троллейбус Победы проехал по городу", NewsCategory.HOLIDAYS.value),
    ("праздничные мероприятия ко Дню Победы", NewsCategory.HOLIDAYS.value),
    ("концерт к дню города", NewsCategory.HOLIDAYS.value),
    ("поздравление с новым годом", NewsCategory.HOLIDAYS.value),
    ("на площади прошёл парад в честь 9 мая", NewsCategory.HOLIDAYS.value),
    ("салют состоялся на набережной", NewsCategory.HOLIDAYS.value),
    ("в парке установили ёлку", NewsCategory.HOLIDAYS.value),
    ("школьники участвовали в праздничной линейке", NewsCategory.HOLIDAYS.value),
    ("прошёл фестиваль уличной еды ко Дню города", NewsCategory.HOLIDAYS.value),
    ("дети пели и танцевали на празднике двора", NewsCategory.HOLIDAYS.value),

    # Образование
    ("дети отдыхают в пришкольных лагерях", NewsCategory.EDUCATION.value),
    ("учителя получили награды", NewsCategory.EDUCATION.value),
    ("в колледже начались занятия", NewsCategory.EDUCATION.value),
    ("в детском саду открыли новую группу", NewsCategory.EDUCATION.value),
    ("приём в университет начнётся в июне", NewsCategory.EDUCATION.value),
    ("школьники сдают экзамены", NewsCategory.EDUCATION.value),
    ("лагерь 'Айно' нуждается в реконструкции", NewsCategory.EDUCATION.value),
    ("школьники участвуют в олимпиадах", NewsCategory.EDUCATION.value),
    ("в вузе запустили новую образовательную программу", NewsCategory.EDUCATION.value),
    ("начались подготовительные курсы для абитуриентов", NewsCategory.EDUCATION.value),
    ("лагерь 'Старт' передан в федеральную собственность", NewsCategory.EDUCATION.value),
    ("родителям рассказали о доступности летнего отдыха", NewsCategory.EDUCATION.value),

    # Происшествия
    ("в центре Петрозаводска нашли повешенного мужчину", NewsCategory.INCIDENTS.value),
    ("в страшной аварии погиб водитель", NewsCategory.INCIDENTS.value),
    ("пожар уничтожил дом и перекинулся на лес", NewsCategory.INCIDENTS.value),
    ("байкер влетел в легковушку", NewsCategory.INCIDENTS.value),
    ("водитель маршрутки снес знак", NewsCategory.INCIDENTS.value),
    ("произошло смертельное ДТП на шоссе", NewsCategory.INCIDENTS.value),
    ("в доме обнаружен труп мужчины", NewsCategory.INCIDENTS.value),
    ("на трассе столкнулись три автомобиля", NewsCategory.INCIDENTS.value),
    ("в Лахденпохье сгорел жилой дом", NewsCategory.INCIDENTS.value),
    ("полиция ищет молодого человека с татуировкой", NewsCategory.INCIDENTS.value),
    ("мужчина угрожал коммунальщикам", NewsCategory.INCIDENTS.value),
    ("в суде продлили арест экс-мэру", NewsCategory.INCIDENTS.value),

    # Общество
    ("изменения в маршрутах автобусов", NewsCategory.SOCIETY.value),
    ("жителям отключат горячую воду на месяц", NewsCategory.SOCIETY.value),
    ("в городе запретили купание в водоёмах", NewsCategory.SOCIETY.value),
    ("владелец электровелосипеда угрожает коммунальщикам", NewsCategory.SOCIETY.value),
    ("в Петрозаводске появятся кольцевые маршруты", NewsCategory.SOCIETY.value),
    ("на улицах города установят новые остановки", NewsCategory.SOCIETY.value),
    ("начался ремонт троллейбусных опор", NewsCategory.SOCIETY.value),
    ("в центре города ограничат движение транспорта", NewsCategory.SOCIETY.value),
    ("администрация сообщает об изменениях маршрутов", NewsCategory.SOCIETY.value),
    ("власти рассказали о туристическом налоге", NewsCategory.SOCIETY.value),
    ("на совещании обсудили развитие Приладожья", NewsCategory.SOCIETY.value),
    ("жители жалуются на отсутствие пляжа", NewsCategory.SOCIETY.value),
    # Общество — изменение маршрутов из-за праздника
    ("в связи с Радоницей изменены автобусные маршруты до кладбищ", NewsCategory.SOCIETY.value),
    ("администрация сообщила об изменении маршрутов автобусов на время праздника", NewsCategory.SOCIETY.value),

    # Культура — музыкальный конкурс
    ("юные артистки стали лауреатами конкурса народных инструментов", NewsCategory.CULTURE.value),
    ("в Санкт-Петербурге прошёл конкурс исполнителей на балалайке и гуслях", NewsCategory.CULTURE.value),
]


# Подготовка датасета
texts, labels = zip(*TRAIN_DATA)
train_dataset = Dataset.from_dict({"text": list(texts), "label": list(labels)})

# Загрузка и обучение модели
model = SetFitModel.from_pretrained("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
trainer = SetFitTrainer(model=model, train_dataset=train_dataset)
trainer.train()

# Сохранение модели
output_path = "saved_models/setfit_news_classifier"
os.makedirs(output_path, exist_ok=True)
model.save_pretrained(output_path)

print(f"Модель успешно обучена и сохранена в: {output_path}")
