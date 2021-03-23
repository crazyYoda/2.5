from random import randint
import colorama
from colorama import Fore, Style

colorama.init()


class Dot:  # Создаем класс для точек в игре
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f'Dot({self.x}, {self.y})'


# Исключения

class GameExceptions(Exception):  # Класс общих исключений
    pass


class OutOfBoardException(GameExceptions):  # Исключение при выстреле за пределы игрового поля
    def __str__(self):
        return 'Вы страляте по суше!!!'


class TwiceShotException(GameExceptions):  # Исключение при выстреле в отстрелянную точку
    def __str__(self):
        return 'Не стреляйте в ту же воронку)))'


class WrongShipStateException(GameExceptions):  # Исключение при неверного положения корабля
    pass


# Класс кораблей

class BattleShip:
    def __init__(self, bow, length, orient):
        self.bow = bow
        self.length = length
        self.orient = orient
        self.lives = length

    @property
    def parts(self):
        ship_parts = []
        for i in range(self.length):
            cur_x = self.bow.x
            cur_y = self.bow.y

            if self.orient == 0:
                cur_x += i
            elif self.orient == 1:
                cur_y += i
            ship_parts.append(Dot(cur_x, cur_y))
        return ship_parts

    def salvo(self, shot):
        return shot in self.parts


# Класс игровое поле

class GameField:
    def __init__(self, hid=False, size=6):
        self.size = size  # размер игрового поля
        self.hid = hid  # скрывать или не скрывать доску

        self.count = 0  # количество пораженных кораблей

        self.field = [['0'] * size for _ in range(size)]  # содержит в себе сетку, которая хранит состояние

        self.busy = []  # занятые или стрелянные точки
        self.all_ships = []  # список кораблей на поле

    def __str__(self):  # Рисуем игровое поле
        g_table = ''
        g_table += '   | 1 | 2 | 3 | 4 | 5 | 6 | \n - - - - - - - - - - - - - -'
        for i, row in enumerate(self.field):
            g_table += f'\n{i + 1}  | ' + ' | '.join(row) + ' |'

        if self.hid:
            g_table = g_table.replace('■', '0')
        return g_table

    def out_of_field(self, point):  # проверка выхода за поле
        return not ((0 <= point.x < self.size) and (0 <= point.y < self.size))

    def contour(self, ship, verb = False):
        # в списке near находятся сдвиги относительно точек корабля (контур)
        near = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for i in ship.parts:
            for dx, dy in near:
                cur = Dot(i.x + dx, i.y + dy)
                if not (self.out_of_field(cur)) and cur not in self.busy:
                    if verb:
                        self.field[cur.x][cur.y] = '.'
                    self.busy.append(cur)

    # добавляем корабль
    def add_ship(self, ship):
        for d in ship.parts:
            if self.out_of_field(d) or d in self.busy:
                raise WrongShipStateException()
        for d in ship.parts:
            self.field[d.x][d.y] = '■'
            self.busy.append(d)
        self.all_ships.append(ship)
        self.contour(ship)

    # Метод для залпа
    def shot(self, d):
        if self.out_of_field(d):  # проверяем в поле ли точка
            raise OutOfBoardException()

        if d in self.busy:  # проверяем не занята ли точка
            raise TwiceShotException()  # если занята выбрасываем исключение

        self.busy.append(d)  # занимаем точку

        for ship in self.all_ships:
            if d in ship.parts:
                ship.lives -= 1
                self.field[d.x][d.y] = 'X'
                if ship.lives == 0:
                    self.count += 1
                    self.contour(ship, verb = True)
                    print(Fore.RED + '!!! TERMINATED !!!')
                    print(Style.RESET_ALL)
                    return False
                else:
                    print(Fore.RED + '!!! Ранение !!!')
                    print(Style.RESET_ALL)
                    return True
        # если корабль не поражен то ставим на место выстрела точку
        self.field[d.x][d.y] = '.'
        print(Fore.YELLOW + '!!! ПРОМАХ !!!')
        print(Style.RESET_ALL)
        return False

    def begin(self):
        self.busy = []  # обнуление списка busy при начале игры

    def defeat(self):
        return self.count == len(self.all_ships)


class Player:
    def __init__(self, board, enemy):
        self.board = board
        self.enemy = enemy

    def ask(self):
        raise NotImplementedError()

    def move(self):
        while True:
            try:
                target = self.ask()
                repeat = self.enemy.shot(target)
                return repeat
            except GameExceptions as e:
                print(e)


class AI(Player):
    def ask(self):
        d = Dot(randint(0, 5), randint(0, 5))
        print(f'Ходит машина: {d.x + 1} {d.y + 1}')
        return d


class User(Player):
    def ask(self):
        while True:
            cords = input('Ваш выстрел, капитан: ').split()

            if len(cords) != 2:
                print(Fore.RED + ' Наводчику нужны точные координаты! ')
                print(Style.RESET_ALL)
                continue

            x, y = cords

            if not (x.isdigit()) or not (y.isdigit()):
                print(Fore.RED + ' Кэп, нужны только числа! ')
                print(Style.RESET_ALL)
                continue

            x, y = int(x), int(y)

            return Dot(x - 1, y - 1)


# Создаем класс игры и генерации досок


class Battle:

    def try_board(self):
        lens = [3, 2, 2, 1, 1, 1, 1]
        board = GameField(size = self.size)
        attempts = 0
        for j in lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = BattleShip(Dot(randint(0, self.size), randint(0, self.size)), j, randint(0, 1))
                try:
                    board.add_ship(ship)
                    break
                except WrongShipStateException:
                    pass
        board.begin()
        return board

    def random_board(self):
        board = None
        while board is None:
            board = self.try_board()
        return board

    def __init__(self, size = 6):
        self.size = size
        user_board = self.random_board()
        comp_board = self.random_board()
        comp_board.hid = True

        self.ai = AI(comp_board, user_board)
        self.user = User(user_board, comp_board)

    def intro(self):
        print('*' * 45)
        print('|{: >27}'.format(Fore.BLUE + 'SEA BATTLE'), '               |')
        print('|{: >30}'.format(Fore.BLUE + 'TITAN COLLISION'), '            |')
        print(Style.RESET_ALL)
        print('*' * 45)
        print()
        print('-' * 45)
        print('|--     {: >21}'.format('Условие правильной стрельбы:'), '     --|')
        print('|--    {: >21}'.format('Формат ввода координат - X и Y'), '    --|')
        print('|--{: >21}'.format(' (Х - номер строки, Y - номер столбца)'), '--|')
        print('-' * 45)

    def print_fields(self):
        print('-' * 20)
        print('Поле капитана:')
        print(self.user.board)
        print('-' * 20)
        print('Поле врага:')
        print(self.ai.board)
        print('-' * 20)

    def loop(self):  # игровой цикл
        num = 0  # номер хода
        while True:
            if num % 2 == 0:
                self.print_fields()
                print('Ход капитана!')
                repeat = self.user.move()
            else:
                print('Ходит враг!')
                repeat = self.ai.move()
            if repeat:
                num -= 1

            if self.ai.board.defeat():
                self.print_fields()
                print('-' * 20)
                print('Капитан победил!')
                break

            if self.user.board.defeat():
                self.print_fields()
                print('-' * 20)
                print('Победа машины!')
                break
            num += 1

    def start(self):
        self.intro()
        self.loop()

