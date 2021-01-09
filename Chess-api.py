import chess
import requests
import json
from bs4 import BeautifulSoup
import lxml
import re

def print_json(r):
    parsed_json = json.loads(r)
    return parsed_json

def show_commands():
    print('These are the available commands:\n'
          'exit              Stop program.\n'
          'back              Undo a move.\n'
          'start variant     Start a variant of the current game.\n'
          'stop variant      Stop a current variant.\n'
          'master            Change the analysis mode to master games.\n'
          'normal            Change the analysis mode to normal games.\n'
          'show [1-4]        Show the selected famous match.\n'
          'help              See the commands again.\n')
    return None


class Consulta():
    def __init__(self, tablero=chess.Board()):
        self._board = tablero

    def show_board(self):
        print(self._board)

    def show_board_unicode(self):
        print(self._board.unicode(borders=True))

    def _special_move(self, move):  #Only for scrapping pgn
        self._board.push_san(move)

    def make_move(self, move):
        if not (4 <= len(move) <= 5):
            print('Say some valid coordinates.\n')
            return None
        mov_splitted = list(move)
        if mov_splitted[0] not in list(
                'abcdefgh') or mov_splitted[2] not in list('abcdefgh') or int(
                    mov_splitted[1]) not in [*range(1, 9, 1)] or int(
                        mov_splitted[3]) not in [*range(1, 9, 1)]:
            print(mov_splitted)
            print('Say some valid coordinates.\n')
            return None
        if len(move) == 5 and mov_splitted[4] not in list('rnbqRNBQ'):
            print('Promotion not valid.\n')
            return None

        movement = chess.Move.from_uci(str(move))
        if movement in self._board.legal_moves:
            self._board.push(movement)

            self.show_board_unicode()

            print()

            print('Good Move')

            print('-----------------------------------------')

        else:
            print('Invalid move.\n')

    def lichess_call(self, bdatos):
        movimientos = {} 

        if bdatos == 'master':     
          url = 'https://explorer.lichess.ovh/master?fen=' + self._fen()

        elif bdatos == 'normal':
          url = 'https://explorer.lichess.ovh/lichess?variant=standard&speeds[]=blitz&speeds[]=rapid&speeds[]=classical&ratings[]=2200&ratings[]=2500&fen=' + self._fen()
        
        r = requests.get(url)
        moves = print_json(r.text)['moves']
        opening = print_json(r.text)['opening']
        top = print_json(r.text)['topGames']

        id_top = []
        for game in top:
            id_top.append(game['id'])
            print(f'{game["white"]["name"]} ({game["white"]["rating"]})\t-\t{game["black"]["name"]} ({game["black"]["rating"]})')
            if game['winner'] == 'white':
                print('Result: 1 - 0')
            elif game['winner'] == 'black':
                print('Result: 0 - 1')
            else:
                print('Result: ½ - ½')
            print()

        if opening is not None:
          self.variacion(opening['eco'])
        for dic in moves:
            totalpart = sum((int(dic['white']), int(dic['draws']),
                             int(dic['black'])))
            movimientos[dic['uci']] = (round(float(dic['white']) / totalpart * 100, 3), 
                                       round(float(dic['draws']) / totalpart * 100, 3),
                                       round(float(dic['black']) / totalpart * 100, 3))
        return movimientos, id_top

    def _fen(self):
        return str(self._board.fen())

    def new_game(self):
        self._board.reset()

    def back(self):
        self._board.pop()
        self.show_board_unicode()

    def ini_variant(self):
        self._board_antiguo = self._board.copy()
        self.show_board_unicode()

    def stop_variant(self):
        self._board = self._board_antiguo
        self.show_board_unicode()

    def set_fen(self, fen):
        self._board.set_board_fen(fen)
        self.show_board_unicode()

    def variacion(self, ide):
        url = 'https://www.365chess.com/eco/' + ide
        src = requests.get(url)
        soup = BeautifulSoup(src.content, 'lxml')
        subvariantes = soup.find('div', id='rel_ops2')
        variaciones = subvariantes.find_all('li')
        print('Possible variations:')
        print()
        for v in variaciones:
            nombre = v.find('a').text
            print(nombre,':')
            print(v.text.strip(nombre))
            print('-----------')

    def show_top_game(self, id_list, num):
        if num > len(id_list):
          print('Non-existent game.\n')
          return None
        
        self._original_board = self._board.copy()
        
        self.new_game()
        self.show_board_unicode()

        url = 'https://explorer.lichess.ovh/master/pgn/' + id_list[num-1]
        r = requests.get(url).text
        game = re.findall(r'1\. .+', r)
        game = game[0].split()
        move = input('Insert an empty string to see the next move or "exit" to return to your match:')
        
        contador = 1
        while move != 'exit':
            if contador % 3 == 0:
                contador += 1

            self._special_move(game[contador])
            self.show_board_unicode()
            print(f'{game[contador]} was played.\n')
            contador += 1

            if contador == len(game)-1:
                print('The match has finished.')
                break

            move = input('¿Shall we continue? ')
            print()

        self._board = self._original_board
        self.show_board_unicode()

if __name__ == '__main__':
    show_commands()
    board = Consulta()
    board.new_game()
    ini_variant = False
    print()
    print()
    bdatos = input('¿What database do you want to use? (master or normal): ')
    while bdatos != "master" and bdatos != "normal":
      print('Choose a correct database.\n')
      bdatos = input('¿What database do you want to use? (master or normal): ')
    print()
    
    board.show_board_unicode()
    print()

    while True:

        movimientos, id_top = board.lichess_call(bdatos)

        print('Move \tWhite \t\tDraw \t\tBlack')
        print()

        for mov, porcentajes in movimientos.items():
            print(f'{mov} \t{"{0:.3f}".format(porcentajes[0])} % \t{"{0:.3f}".format(porcentajes[1])} % \t{"{0:.3f}".format(porcentajes[2])} %')
            print()

        mov = input('¿What move do you want to make?: ')
        print()

        if mov == 'exit':
            print('------------------------------------')
            print('Thanks for using this motor.')
            print('------------------------------------')
            break

        elif mov == 'back':
            if int(board._fen().split()
                   [-1]) == 1 and board._fen().split()[1] == 'w':
                print('You have not made a move yet.')
            else:
                prueba = board.back()

        elif mov == 'start variant':
            if ini_variant == False:
                board.ini_variant()
                ini_variant = True
            else:
                print('You are already in an initialized variant.')

        elif mov == 'stop variant':
            if ini_variant == True:
                board.stop_variant()
                ini_variant == False
            else:
                print('There is no variant initialized.')
        
        elif mov == 'master':
          bdatos = 'master'

        elif mov == 'normal':
          bdatos = 'normal'

        elif mov == 'help':
          show_commands()

        elif mov == 'show 1' or mov == 'show 2' or mov == 'show 3' or mov == 'show 4':
            if bdatos == 'master':
                board.show_top_game(id_top, int(mov[-1]))
            else:
                print('Unofficial matches cannot be seen.')

        else:
            board.make_move(mov)
