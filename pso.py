"""Алгоритм оптимизации отпусков"""


import psycopg2
from datetime import datetime, timedelta, date
from config import HOST, USER, PASSWORD, DB_NAME

# Подключение к базе данных
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=USER,
    password=PASSWORD,
    host=HOST,
)


# Параметры оптимизации
DAYS_DENSITY = 7  # Плотность перераспределения отпуска (стандартно 7, меньше - отпуска ближе к друг другу)
MAX_DEPARTMENT_CAPACITY = 0.3  # Максимальная емкость отдела (30%)
POPULATION_SIZE = 0  # Размер популяции, определяется в ходе работы
MAX_GENERATIONS = 100  # Количество поколений


# Сведения о пожеланиях
VACATIONS_IDS: list[int] = []
WISHED_USER_IDS: list[int] = []
VACATION_LENGTH: list[int] = []
START_DAY: list[int] = []
START_MONTH: list[int] = []

# Функция для расчета пригодности (fitness) отпуска
def calculate_fitness(vacation, department_counts):
    department = vacation['department']
    department_count = department_counts.get(department, 0)
    return department_count / MAX_DEPARTMENT_CAPACITY

# Функция для генерации случайного отпуска
def generate_vacation(wish_uuid: int, vac_len: int, day_start: int, month_start: int):
    cursor = conn.cursor()
    cursor.execute("SELECT department FROM unusedvacs WHERE uuid = %s" % (wish_uuid,))
    uuid_department = cursor.fetchall()
    cursor.close()
    return {
        'uuid': wish_uuid,
        'department': uuid_department[0],
        'datestart': datetime(date.today().year+1, month=month_start, day=day_start),
        'vacationlength': vac_len
    }

# Функция для создания начальной популяции
def create_initial_population():
    population = []

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM wishes")
    global VACATIONS_IDS, POPULATION_SIZE, WISHED_USER_IDS, VACATION_LENGTH, START_DAY, START_MONTH
    request_data = cursor.fetchall()
    VACATIONS_IDS = [int(vacid[0]) for vacid in request_data]
    WISHED_USER_IDS = [int(wishuuid[1]) for wishuuid in request_data]
    for vaclen in request_data:
        match vaclen[2]:
            case 'longvacation': VACATION_LENGTH.append(14)
            case 'mediumvacation': VACATION_LENGTH.append(7)
            case 'smallvacation': VACATION_LENGTH.append(1)
    START_DAY = [int(startday[3]) for startday in request_data]
    START_MONTH = [int(startmonth[4]) for startmonth in request_data]
    POPULATION_SIZE = len(VACATIONS_IDS)
    cursor.close()
    for i in range(POPULATION_SIZE):
        vacation = generate_vacation(WISHED_USER_IDS[i], VACATION_LENGTH[i], START_DAY[i],
                                     START_MONTH[i])
        population.append(vacation)
    return population

# Функция для выполнения алгоритма роя пчел
def bee_algorithm():
    # Создание начальной популяции
    population = create_initial_population()

    # Выполнение цикла поколений
    for _ in range(MAX_GENERATIONS):
        # Расчет пригодности для каждого отпуска
        department_counts = {}
        for vacation in population:
            department = vacation['department']
            department_counts[department] = department_counts.get(department, 0) + 1
            fitness = calculate_fitness(vacation, department_counts)
            vacation['fitness'] = fitness

        # Сортировка популяции по убыванию пригодности
        population.sort(key=lambda x: x['fitness'], reverse=True)

        # Отбор лучших отпусков (пчел-исследователей)
        top_vacations = population[:int(POPULATION_SIZE * 0.2)]

        # Перебор лучших отпусков и обновление даты начала отпуска
        for vacation in top_vacations:
            vacation['datestart'] += timedelta(DAYS_DENSITY)
            '''for bee in population:
                if bee['uuid'] == vacation['uuid']:
                    bee['datestart'] += timedelta(DAYS_DENSITY)
            print('изменение внесено')'''

    # Запись оптимизированных дат начала отпусков в базу данных
    cursor = conn.cursor()
    for vacation in population:
        uuid = vacation['uuid']
        date_start = vacation['datestart']
        nextyear = str(date_start)
        nextyear = nextyear.replace("2025", "2024")
        date_end = date_start + timedelta(days=vacation['vacationlength'] - 1)
        nextyear2 = str(date_end)
        nextyear2 = nextyear2.replace("2025", "2024")
        cursor.execute(
            "INSERT INTO finaldates (uuid, datestart, datetill) VALUES (%s, %s, %s)",
            (uuid, nextyear, nextyear2)
        )
    # cursor.execute("DELETE FROM finaldates")
    # cursor.execute("DELETE FROM wishes")
    conn.commit()
    cursor.close()