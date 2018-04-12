from hiveminder import algo_player
import copy
import sys
from timeit import default_timer as timer
import random
from datetime import datetime
import numpy as np

@algo_player(name="Best algo",
             description="")
def template_algo(board_width, board_height, hives, flowers, inflight, crashed,
                  lost_volants, received_volants, landed, scores, player_id, game_id, turn_num):
                  
    start = timer()
    
    state = State()
    state.hives = hives
    state.flowers = flowers
    state.inflight = inflight

    moves = available_moves(state)
    moves['0'] = 'p'

    size = len(moves) * 3 #shortcut, not to count all elements of moves

    detailed = [[] for y in range(size)]
    queenBee = [False] * size
    volants = [None] * size
    actions = [0] * size
    temp = [None] * size
    firstPoints = [None] * size

    reachedEnd = False

    i = 0
    for volant_id, actions2 in moves.items():
        for action in actions2:
            if volant_id != "0":
                if inflight[volant_id][0] == "QueenBee":
                    queenBee[i] = True

            firstPoints[i], temp[i] = next_state(copy.deepcopy(state), action, volant_id, turn_num)
            volants[i] = volant_id
            actions[i] = action
            i += 1

    a = 0
    while a < i and (timer() - start < 0.15):
        if queenBee[a]:
            result = try_random_moves(2, copy.deepcopy(temp[a]), turn_num)
            detailed[a].append(result) 
        a += 1

    while (timer() - start < 0.15):
        a = 0
        while a < i and (timer() - start < 0.15):
            result = try_random_moves(2, copy.deepcopy(temp[a]), turn_num)
            detailed[a].append(result)
            if queenBee[a]:
                result = try_random_moves(2, copy.deepcopy(temp[a]), turn_num)
                detailed[a].append(result) 
            a += 1
    

    highestScore = float('-inf')
    highestNumber = 0
    a = 0

   

    while a < i and ((a < 3) or (timer() - start <= 0.19)):
        detailed[a].sort()
        while len(detailed[a]) > 5:
            detailed[a] = detailed[a][len(detailed[a])//2:]
        if detailed[a] and highestScore < np.mean(detailed[a]) + firstPoints[a] * 2:
            highestScore = np.mean(detailed[a]) + firstPoints[a] * 2
            highestNumber = a
        a += 1



    bestAction = actions[highestNumber]
    bestVolantId = volants[highestNumber]
 
    if bestAction == "p": #pass
        return None
    elif bestAction == "c": #create_hive
        return dict(entity=bestVolantId, command="create_hive")
    elif bestAction == "f": #flower
        return dict(entity=bestVolantId, command="flower")
    else:
        return dict(entity=bestVolantId, command=bestAction)


@template_algo.on_start_game
def start_game(board_width, board_height, hives, flowers, players, player_id, game_id, game_params):
	
    return None

@template_algo.on_game_over
def game_over(board_width, board_height, hives, flowers, inflight, crashed,
              lost_volants, received_volants, landed, scores, player_id, game_id, turns):

    return None

class State:
    hives = []
    flowers = []
    inflight = {}
    score = 0
    boardWithHives = None
    boardWithFlowers = None


new_headings = {0: [60, -60],
        60:    [120, 0],
        120:   [180, 60],
        180:   [-120, 120],
        -120:  [-60, 180],
        -60:   [0, -120], 
        }   


def try_random_moves(count, state, turn_num):
    pointsChange = 0
    for _ in range(count):
        moves = available_moves(state)
        moves['0'] = 'p'
        randomKey = random.choice(list(moves.keys()))
        randomAction = random.choice(moves[randomKey])
        temp, state = next_state(state, randomAction, randomKey, turn_num)
        pointsChange += temp
    return pointsChange / count

def new_position(x, y, direction):
    if direction == 0:
        return x, y + 1
    elif direction == 180:
        return x, y - 1
    elif direction == -60:
        if x % 2 == 0:
            return x - 1, y + 1
        else:
            return x - 1, y
    elif direction == 60:
        if x % 2 == 0:
            return x + 1, y + 1
        else:
            return x + 1, y
    elif direction == -120:
        if x % 2 == 1:
            return x - 1, y - 1
        else:
            return x - 1, y
    elif direction == 120:
        if x % 2 == 1:
            return x + 1, y - 1
        else:
            return x + 1, y

            
def available_moves(state): #available moves without seeds turning
    moves = {}
       
    for volant_id, volant in state.inflight.items():
        if volant[0] == "Seed":
            moves[volant_id] = ["f"]
        else:
            moves[volant_id] = [new_headings[ volant[3] ][0], new_headings[ volant[3] ][1]]        
            if volant[0] == "QueenBee":
                moves[volant_id].append("c")
    return moves

def available_moves2(state):
    moves = {}
       
    for volant_id, volant in state.inflight.items():
    
        moves[volant_id] = []
        moves[volant_id].append(new_headings[ volant[3] ][0])
        moves[volant_id].append(new_headings[ volant[3] ][1])
        
        if volant[0] == "QueenBee":
            moves[volant_id].append("c")
        elif volant[0] == "Seed":
            moves[volant_id].append("f")    
    return moves
    

def next_state(state, action, volant_id, stateRound):
    hives = state.hives
    score = state.score
    inflight = state.inflight
    flowers = state.flowers
    boardWithHives = state.boardWithHives
    boardWithFlowers = state.boardWithFlowers

    pointChange = 0

    boardWithHives = [[None]*8 for i in range(8)]
    for hive in hives:
        boardWithHives[ hive[0] ][ hive[1] ] = hive
    
    for flower in copy.deepcopy(flowers): #delete wilted flowers
        if stateRound > flower[5]: #if round is bigger than flower's lifespan + no. round it appeared in
            flowers.remove(flower)
            pointChange -= 50

    if (boardWithFlowers == None):
        boardWithFlowers = [[None]*8 for i in range(8)]
        for flower in flowers:
            boardWithFlowers[ flower[0] ][ flower[1] ] = flower

    if action == "p": #pass
        pass
    elif action == "c": #create_hive
        if (boardWithHives[ inflight[ volant_id ][ 1 ] ][ inflight[ volant_id ][ 2 ] ] != None):
            pointChange += -5000
        if (boardWithFlowers[ inflight[ volant_id ][ 1 ] ][ inflight[ volant_id ][ 2 ] ] != None):
            pointChange += -100
        
        xHive = inflight[ volant_id ][ 1 ] 
        yHive = inflight[ volant_id ][ 2 ]

        hives.append([ inflight[ volant_id ][ 1 ],  inflight[ volant_id ][ 2 ], 0])
        inflight.pop(volant_id)
        pointChange += 200
 
        if xHive % 2 == 0:
            listX = [xHive,     xHive,     xHive - 1, xHive + 1, xHive - 1, xHive + 1]
            listY = [yHive + 1, yHive - 1, yHive + 1, yHive + 1, yHive,     yHive    ]
        else:
            listX = [xHive,     xHive,     xHive - 1, xHive + 1, xHive - 1, xHive + 1]
            listY = [yHive + 1, yHive - 1, yHive,     yHive    , yHive - 1, yHive - 1]

        notSurrounded = True
        for x, y in zip(listX, listY):
            if (x > -1 and x < 8 and y > -1 and y < 8):
                if (boardWithHives[x][y] != None):
                    notSurrounded = False

        if notSurrounded:
            pointChange += 1500



        for hive in hives:
            boardWithHives[ hive[0] ][ hive[1] ] = hive
        for flower in flowers:
            boardWithFlowers[ flower[0] ][ flower[1] ] = flower
    elif action == "f": #flower
        if (boardWithHives[ inflight[ volant_id ][ 1 ] ][ inflight[ volant_id ][ 2 ] ] != None):
            pointChange += -500
        if (boardWithFlowers[ inflight[ volant_id ][ 1 ] ][ inflight[ volant_id ][ 2 ] ] != None):
            pointChange += -100

        xFlower = inflight[ volant_id ][ 1 ] 
        yFlower = inflight[ volant_id ][ 2 ] 

        flowers.append([ inflight[ volant_id ][ 1 ],  inflight[ volant_id ][ 2 ], -1, 1, 0, 300])
        pointChange += 50
        inflight.pop(volant_id)


        if xFlower % 2 == 0:
            listX = [xFlower,     xFlower,     xFlower - 1, xFlower + 1, xFlower - 1, xFlower + 1]
            listY = [yFlower + 1, yFlower - 1, yFlower + 1, yFlower + 1, yFlower,     yFlower    ]
        else:
            listX = [xFlower,     xFlower,     xFlower - 1, xFlower + 1, xFlower - 1, xFlower + 1]
            listY = [yFlower + 1, yFlower - 1, yFlower,     yFlower    , yFlower - 1, yFlower - 1]

        for x, y in zip(listX, listY):
            if (x > -1 and x < 8 and y > -1 and y < 8):
                if (boardWithHives[x][y] != None):
                    pointChange += 2

        for hive in hives:
            boardWithHives[ hive[0] ][ hive[1] ] = hive
        for flower in flowers:
            boardWithFlowers[ flower[0] ][ flower[1] ] = flower
    else:
        inflight[volant_id][3] = action



    boardWithBees = [[None]*8 for i in range(8)] #board for detecting crashes

    # compute next board state
    for key, volant in copy.copy(inflight).items():
        volant[1], volant[2] = new_position(volant[1], volant[2], volant[3])
        

        # check if volant did not leave the board
        if ((volant[1] < 0) or (volant[1] > 7) or (volant[2] < 0) or (volant[2] > 7)):
            inflight.pop(key)
            continue
            

        if (volant[0] == "Bee") or (volant[0] == "QueenBee"):
            if (volant[0] == "QueenBe"):
                pointChange += 10 #artifical to keep queen bee alive
            volant[4] -= 1
            if (boardWithHives[ volant[1] ][ volant[2] ] != None): #if volant is over hive, add points and remove volant
                pointChange += volant[6] * 2 + boardWithHives[volant[1]][volant[2]][2]/100# 2 points per piece of nectar + motivation to add up to the one with highest acumulation 
                inflight.pop(key)
            elif (volant[4] < 0):
                inflight.pop(key)
                pointChange += -3
            elif (boardWithBees[ volant[1] ][ volant[2] ] != None):
                inflight.pop(boardWithBees[ volant[1] ][ volant[2] ])
                inflight.pop(key)
                pointChange += -6
                boardWithBees[ volant[1] ][ volant[2] ] = None
            elif (boardWithFlowers[ volant[1] ][ volant[2] ] != None): #if over flower
                flowerBelow = boardWithFlowers[ volant[1] ][ volant[2] ]

                maxCollection = min(flowerBelow[3], 5-inflight[key][6])
                if maxCollection > 0:
                    pointChange += maxCollection/10

                inflight[key][6] += maxCollection #collect nectar
                inflight[key][4] += 25 * flowerBelow[3] #increase bee's life

                flowerBelow[4] += 1 # number of visits already
                flowerBelow[5] += 10 # persistence

                if flowerBelow[4] % 10 == 0 and flowerBelow[4] > 0: #if tenth visit, increase nectar given (max 3) and put seed
                    if flowerBelow[3] < 3:
                        flowerBelow[3] += 1 
                    inflight[str(datetime.now())] = ["Seed", volant[1], volant[2], volant[3]]
            else:
                boardWithBees[ volant[1] ][ volant[2] ] = key 
                #artifical 
                listX, listY = cellsOnCourse(volant[1], volant[2], volant[3])
                if volant[6] == 0: ##if no nectar, promote flying onto flower
                    for x, y in zip(listX, listY):
                        if (boardWithFlowers[x][y] != None):
                            pointChange += 1 / 11 #can't be too important, as algo should never prefer pointing bee onto flower to e.g. losing different one
                            break #no need to check what's behind
                else: #if with nectar, promote flying onto hive
                    for x, y in zip(listX, listY):
                        if (boardWithHives[x][y] != None):
                            pointChange += volant[6] / 10 #better to point bee with nectar onto hive, than bee onto flower to grab it
                            break #no need to check what's behind
    sizeOfInflight = len(inflight) 
    if sizeOfInflight > 7:
        pointChange -= (sizeOfInflight/10) # artifical, reduce number of volants if you won't lose points by doing so
    if sizeOfInflight > 11:
        pointChange -= (sizeOfInflight/10) 
    if sizeOfInflight > 15:
        pointChange -= (sizeOfInflight/8) 
    if sizeOfInflight > 19:
        pointChange -= (sizeOfInflight/8) 

    return pointChange, state

def cellsOnCourse(x, y, heading):
    xList = []
    yList = []

    xBuffer = x
    yBuffer = y

    while (7 > xBuffer and xBuffer > 0) and (7 > yBuffer and yBuffer > 0):
        xBuffer, yBuffer = new_position(xBuffer, yBuffer, heading)
        xList.append(xBuffer)
        yList.append(yBuffer)

    return xList, yList
