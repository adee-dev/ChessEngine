"""
Main driver file
"""

import pygame as p
import ChessEngine, SmartMoveFinder
from multiprocessing import Process, Queue

# p.init()
BOARD_WIDTH = BOARD_HEIGHT = 512    # 400 is also a good option
MOVE_LOG_PANEL_WIDTH = 300
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT

DIMENSION = 8           # It is 8x8 chessboard
SQ_SIZE = BOARD_HEIGHT//DIMENSION
MAX_FPS = 15            # for animation later on
IMAGES = {}

''' 
Init a global dict of imgs and called exactly once in main
'''


def loadImages():
    pieces = ['bR', 'bN', 'bB', 'bQ', 'bK',
              'bp', 'wp', 'wR', 'wN', 'wB', 'wQ', 'wK']

    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(
            'Chess/images/'+piece+'.png'), (SQ_SIZE, SQ_SIZE))


'''
Main driver and handle user input and updating graphics
'''


def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH+MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color('white'))
    moveLogFont = p.font.SysFont('Arial', 18, False, False)
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    animate = False  # flag variable for when we should animate a move
    moveMade = False  # flag var when a move is made
    # print(gs.board)   #check board
    loadImages()  # Do it only once, before while loop
    running = True
    sqSelected = ()  # keep track of last click of user (tuple: (row, col))
    playerClicks = []  # keep track f player clicks (two tuples: [(6,4),(4,4)])
    gameOver = False
    playerOne = True   #if human is playing white, it will be true. If AI playing, then false
    playerTwo = True  #same as above for black #set it true for 2 player game
    AIThinking = False
    moveFinderProcess =None
    
    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
        
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            # mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver:
                    location = p.mouse.get_pos()    # (x, y) coordinates of mouse
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if sqSelected == (row, col) or col >=8:  # user selected same sq twice
                        sqSelected = ()  # deselect sq
                        playerClicks = []  # clear player clicks
                    else:
                        sqSelected = (row, col)
                        # append for both 1st and 2nd click
                        playerClicks.append(sqSelected)
                    if len(playerClicks) == 2 and humanTurn:  # after 2nd click
                        move = ChessEngine.Move(
                            playerClicks[0], playerClicks[1], gs.board)
                        print(move.getChessNotation())
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                sqSelected = ()  # reset user clicks
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]

            # key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # undo by press' z
                    gs.undoMove()
                    moveMade = True
                    animate = False
                    gameOver = False

                if e.key == p.K_r:  # reset the board when 'r' is pressed
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver=False
                    
        #AI move finder logic
        if not gameOver and not humanTurn:
            if not AIThinking:
                AIThinking=True
                print('thinking...')
                returnQueue = Queue()   #used to pass data between threads
                moveFinderProcess = Process(target=SmartMoveFinder.findBestMove, args=(gs, validMoves, returnQueue))
                moveFinderProcess.start()   #calls findBestMove(gs, validMoves, returnQueue)
                # AIMove = SmartMoveFinder.findBestMove(gs, validMoves)
                
            if moveFinderProcess.is_alive():
                # print('done thinking!')
                AIMove = returnQueue.get()
                if AIMove is None:
                    AIMove = SmartMoveFinder.findRandomMove(validMoves)
                print('done thinking!')
                gs.makeMove(AIMove)
                moveMade=True
                animate=True
                AIThinking=False

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False

        drawGameState(screen, gs, validMoves, sqSelected, moveLogFont)

        if gs.checkmate or gs.stalemate:
            gameOver = True
            drawEndGameText(
                screen, '...Stalemate...' if gs.stalemate else 'BLACK wins by checkmate!' if gs.whiteToMove else 'WHITE wins by checkmate!')


        clock.tick(MAX_FPS)
        p.display.flip()


'''
respo for draw' graphics in curr gs
'''


def drawGameState(screen, gs, validMoves, sqSelected, moveLogFont):
    drawBoard(screen)  # draw squares on board
    highlightSquare(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)  # draw pieces on squares
    drawMoveLog(screen, gs, moveLogFont)


'''
Draw squares on board
'''


def drawBoard(screen):
    global colors
    colors = [p.Color('white'), p.Color('darkgray')]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c) % 2)]
            p.draw.rect(screen, color, p.Rect(
                c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


'''
highlight sq selected and moves for pieces selected
'''


def highlightSquare(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        # sqSelected is a piece that can be moved
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'):
            # highlight selected sq
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            # transparency value: 0 -> transparent and 255 -> opaque
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            # highlight moves from that square
            s.fill(p.Color('yellow'))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol*SQ_SIZE, move.endRow*SQ_SIZE))


'''
It draws pieces
'''


def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != '--':     # not empty square
                screen.blit(IMAGES[piece], p.Rect(
                    c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


'''
Draw move log method
'''
def drawMoveLog(screen, gs, font):
    moveLogRect = p.Rect(
        BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('black'), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveString = str(i//2 + 1)+ '. '+str(moveLog[i])+' '
        if i+1 < len(moveLog):  #to make sure black made a move
            moveString += str(moveLog[i+1])+'  '
        moveTexts.append(moveString)
        
    movesPerRow =3
    padding = 5
    textY =padding
    lineSpacing=2
    for i in range(0, len(moveTexts), movesPerRow):
        text = ''
        for j in range(movesPerRow):
            if i+j< len(moveTexts):
                text+=moveTexts[i+j]
        textObject = font.render(text, True, p.Color('white'))
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)
        textY+=textObject.get_height()+lineSpacing

'''
Animating a move
'''


def animateMove(move, screen, board, clock):
    global colors
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10  # frames to move one square
    frameCount = (abs(dR)+abs(dC))*framesPerSquare
    for frame in range(frameCount+1):
        r, c = ((move.startRow+dR*frame/frameCount,
                move.startCol+dC*frame/frameCount))
        drawBoard(screen)
        drawPieces(screen, board)
        # erase piece moved from its ending sq
        color = colors[(move.endRow+move.endCol) % 2]
        endSquare = p.Rect(move.endCol*SQ_SIZE,
                           move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        # draw captured piece onto rectangle
        if move.pieceCaptured != '--':
            if move.isEnpassantMove:
                enpassantRow =move.endRow+1 if move.pieceCaptured[0]=='b' else move.endRow-1
                endSquare = p.Rect(move.endCol*SQ_SIZE,enpassantRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        # draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(
            c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


def drawEndGameText(screen, text):
    font = p.font.SysFont('Helvitca', 45, True, False)
    textObject = font.render(text, 0, p.Color('Black'))
    textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(
        BOARD_WIDTH/2-textObject.get_width()/2, BOARD_HEIGHT/2-textObject.get_height()/2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, p.Color('Cyan'))
    screen.blit(textObject, textLocation.move(4, 4))


if __name__ == '__main__':
    main()
