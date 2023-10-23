"""
Save all info of current game state and determine valid move and move logs
"""


class GameState():
    def __init__(self):
        # board is 8*8 2d list
        # first char rep color b or w: black or white
        # second character represent type
        # '--' rep empty space

        self.board = [
            ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bp' for i in range(8)],
            ['--' for i in range(8)],
            ['--' for i in range(8)],
            ['--' for i in range(8)],
            ['--' for i in range(8)],
            # ['--', '--', '--', 'bp', '--', '--', '--', '--'],
            ['wp' for i in range(8)],
            ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
        ]
        self.whiteToMove = True
        self.moveLog = []
        self.moveFunctions = {'p': self.getPawnMoves, 'R': self.getRookMoves, 'N': self.getKnightMoves,
                              'B': self.getBishopMoves, 'Q': self.getQueenMoves, 'K': self.getKingMoves}
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.enpassantPossible = ()  # ccordinates of sq where en-passant is possible
        self.enpassantPossibleLog = [self.enpassantPossible]
        self.currentCastlingRight = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(
            self.currentCastlingRight.wks, self.currentCastlingRight.bks, self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)]

        # self.protects = [][]
        # self.threatens = [][]
        # self.squaresCanMoveTo [][]

    '''
    Takes a move as para and executes it (This willn't work for casteling, pawn promotion and en-passant)
    '''

    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = '--'
        self.board[move.endRow][move.endCol] = move.pieceMoved
        # log the move so we can undo it later or display history of game
        self.moveLog.append(move)
        self.whiteToMove = not self.whiteToMove  # swap players
        # update kings location if moved
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)

        # pawn promotion
        if move.isPawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0]+'Q'

        # en passant move
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = '--'  # capturing the pawn

        # update enpassantPossible variable
        # only on 2 sq pawn advances
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = (
                (move.startRow+move.endRow)//2, move.startCol)
        else:
            self.enpassantPossible = ()

        # castle move
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # kingside castle
                # moves the rook
                self.board[move.endRow][move.endCol -
                                        1] = self.board[move.endRow][move.endCol+1]
                self.board[move.endRow][move.endCol+1] = '--'  # erase old rook
            else:  # queenside castle
                # moves the rook
                self.board[move.endRow][move.endCol +
                                        1] = self.board[move.endRow][move.endCol-2]
                self.board[move.endRow][move.endCol-2] = '--'  # erase old rook
                
        #
        self.enpassantPossibleLog.append(self.enpassantPossible)

        # update castling rights
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                    self.currentCastlingRight.wqs, self.currentCastlingRight.bqs))

    '''
    Undo the last move
    '''

    def undoMove(self):
        if len(self.moveLog) != 0:  # make sure there is move to undo
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove
            # update kings location if moved
            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)

        # undo en passant move
        if move.isEnpassantMove:
            # leave landing sq blank
            self.board[move.endRow][move.endCol] = '--'
            # print('ok')
            self.board[move.startRow][move.endCol] = move.pieceCaptured
        
        self.enpassantPossibleLog.pop()
        self.enpassantPossible = self.enpassantPossibleLog[-1]

        # undoing castle rights
        self.castleRightsLog.pop()  # get rid of new castling rights from move we are undoing
        # set curr castle rights to last one in list
        self.currentCastlingRight = self.castleRightsLog[-1]

        # undo castle move
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # kingside
                self.board[move.endRow][move.endCol +
                                        1] = self.board[move.endRow][move.endCol-1]
                self.board[move.endRow][move.endCol-1] = '--'
            else:  # queenside
                self.board[move.endRow][move.endCol -
                                        2] = self.board[move.endRow][move.endCol+1]
                self.board[move.endRow][move.endCol+1] = '--'

        # checkmate and stalemate
        self.checkmate = False
        self.stalemate = False

    '''
    Update castling rights given the move
    '''

    def updateCastleRights(self, move):
        if move.pieceMoved == 'wK':
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == 'bK':
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.pieceMoved == 'wR':
            if move.startRow == 7:
                if move.startCol == 0:  # left rook
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7:  # right rook
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == 'bR':
            if move.startRow == 0:
                if move.startCol == 0:  # left rook
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7:  # right rook
                    self.currentCastlingRight.bks = False

        # if rook is captured
        if move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.wks = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.bks = False

    '''
    All moves considering checks
    '''

    def getValidMoves(self):
        tempEnpassantPossible = self.enpassantPossible
        tempCastleRights = CastleRights(
            self.currentCastlingRight.wks, self.currentCastlingRight.bks, self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)  # copy current castling rigtes
        # Naive Algo:
        # 1. gen all possible moves
        moves = self.getAllPossibleMoves()
        if self.whiteToMove:
            self.getCastleMoves(
                self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
        else:
            self.getCastleMoves(
                self.blackKingLocation[0], self.blackKingLocation[1], moves)

        # 2. for each move make them
        # when removing from list go backward through the list
        for i in range(len(moves)-1, -1, -1):
            self.makeMove(moves[i])
            # 3. gen all opponents moves
            # 4. for each opponents move see if they attack your king
            self.whiteToMove = not self.whiteToMove  # switch thruns back
            if self.inCheck():
                # 5. if they do attack king, it's not a valid move
                moves.remove(moves[i])
            self.whiteToMove = not self.whiteToMove  # switch thruns back
            self.undoMove()

        if len(moves) == 0:  # it's either a checkmate or stalemate
            if self.inCheck():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.enpassantPossible = tempEnpassantPossible
        self.currentCastlingRight = tempCastleRights

        return moves  # for now dont worry abt checks

    '''
    dtmn if current player is in check
    '''

    def inCheck(self):
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    '''
    dtmn if enemy can attack sq r,c
    '''

    def squareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove  # switch to the opponent's turn
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove  # switch thruns back
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:  # the square is under attack
                return True
        return False

    '''
    All moves without considering checks
    '''

    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):  # no of rows
            for c in range(len(self.board[r])):  # no of cols in gn row
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    # calls apropriate function based on piece type
                    self.moveFunctions[piece](r, c, moves)
        return moves

    '''
    Get all the pawns moves at row, col and add to the list
    '''

    def getPawnMoves(self, r, c, moves):
        if self.whiteToMove:  # white to move
            if self.board[r-1][c] == '--':  # one sq on advance
                moves.append(Move((r, c), (r-1, c), self.board))
                # 2 sq advance
                if r == 6 and self.board[r-2][c] == '--':
                    moves.append(Move((r, c), (r-2, c), self.board))

            if c-1 >= 0:  # capture to the left
                if self.board[r-1][c-1][0] == 'b':
                    # enemy piece to capture
                    moves.append(Move((r, c), (r-1, c-1), self.board))
                elif (r-1, c-1) == self.enpassantPossible:
                    moves.append(
                        Move((r, c), (r-1, c-1), self.board, isEnpassantMove=True))

            if c+1 <= 7:  # capture to the rigtht
                if self.board[r-1][c+1][0] == 'b':
                    # enmy piece to capture
                    moves.append(Move((r, c), (r-1, c+1), self.board))
                elif (r-1, c+1) == self.enpassantPossible:
                    moves.append(
                        Move((r, c), (r-1, c+1), self.board, isEnpassantMove=True))

        else:  # black pawn moves
            if self.board[r+1][c] == '--':  # one sq on advance
                moves.append(Move((r, c), (r+1, c), self.board))
                # 2 sq advance
                if r == 1 and self.board[r+2][c] == '--':
                    moves.append(Move((r, c), (r+2, c), self.board))

            if c-1 >= 0:  # capture to the left
                if self.board[r+1][c-1][0] == 'w':
                    # enmy piece to capture
                    moves.append(Move((r, c), (r+1, c-1), self.board))
                elif (r+1, c-1) == self.enpassantPossible:
                    moves.append(
                        Move((r, c), (r+1, c-1), self.board, isEnpassantMove=True))
            if c+1 <= 7:  # capture to the rigth
                if self.board[r+1][c+1][0] == 'w':
                    # enmy piece to capture
                    moves.append(Move((r, c), (r+1, c+1), self.board))
                elif (r+1, c+1) == self.enpassantPossible:
                    moves.append(
                        Move((r, c), (r+1, c+1), self.board, isEnpassantMove=True))
        # add pawn promotions later

    '''
    Get all the rook moves at row, col and add to the list
    '''

    def getRookMoves(self, r, c, moves):
        # up, left, down, right
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemyColor = 'b' if self.whiteToMove else 'w'
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0]*i
                endCol = c + d[1]*i
                if 0 <= endRow < 8 and 0 <= endCol < 8:  # on board
                    endPiece = self.board[endRow][endCol]
                    if endPiece == '--':  # empty space valid
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColor:  # enemy piece valid
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))
                        break
                    else:  # friendly/ally piece
                        break
                else:  # off board
                    break

        '''
    Get all the knight moves at row, col and add to the list
    '''

    def getKnightMoves(self, r, c, moves):
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1))
        allyColor = 'w' if self.whiteToMove else 'b'
        for m in knightMoves:
            endRow = r+m[0]
            endCol = c+m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                # not an ally piece (ie, empty or enemy piece)
                if endPiece[0] != allyColor:
                    moves.append(Move((r, c), (endRow, endCol), self.board))

    '''
    Get all the bishop moves at row, col and add to the list
    '''

    def getBishopMoves(self, r, c, moves):
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))  # diagonals moves
        enemyColor = 'b' if self.whiteToMove else 'w'
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0]*i
                endCol = c + d[1]*i
                if 0 <= endRow < 8 and 0 <= endCol < 8:  # on board
                    endPiece = self.board[endRow][endCol]
                    if endPiece == '--':  # empty space valid
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColor:  # enemy piece valid
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))
                        break
                    else:  # friendly/ally piece
                        break
                else:  # off board
                    break

    '''
    Get all the queen moves at row, col and add to the list
    '''

    def getQueenMoves(self, r, c, moves):
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)

    '''
    Get all the king moves at row, col and add to the list
    '''

    def getKingMoves(self, r, c, moves):
        kingMoves = ((-1, -1), (-1, 0), (-1, 1), (0, -1),
                     (0, 1), (1, -1), (1, 0), (1, 1))
        allyColor = 'w' if self.whiteToMove else 'b'
        for i in range(8):
            endRow = r+kingMoves[i][0]
            endCol = c+kingMoves[i][1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                # not an ally piece (ie, empty or enemy piece)
                if endPiece[0] != allyColor:
                    moves.append(Move((r, c), (endRow, endCol), self.board))
        # self.getCastleMoves(r, c, moves, allyColor)

    '''
    Generate all valid moves for king at (r,c) and add tham to list of moves
    '''

    def getCastleMoves(self, r, c, moves):
        if self.squareUnderAttack(r, c):
            return  # cant castle whie in check
        if (self.whiteToMove and self.currentCastlingRight.wks) or (not self.whiteToMove and self.currentCastlingRight.bks):
            self.getKingsideCastleMoves(r, c, moves)
        if (self.whiteToMove and self.currentCastlingRight.wqs) or (not self.whiteToMove and self.currentCastlingRight.bqs):
            self.getQueensideCastleMoves(r, c, moves)

    def getKingsideCastleMoves(self, r, c, moves):
        if self.board[r][c+1] == '--' and self.board[r][c+2] == '--':
            if not self.squareUnderAttack(r, c+1) and not self.squareUnderAttack(r, c+2):
                moves.append(
                    Move((r, c), (r, c+2), self.board, isCastleMove=True))

    def getQueensideCastleMoves(self, r, c, moves):
        if self.board[r][c-1] == '--' and self.board[r][c-2] == '--' and self.board[r][c-3] == '--':
            if not self.squareUnderAttack(r, c-1) and not self.squareUnderAttack(r, c-2):
                moves.append(
                    Move((r, c), (r, c-2), self.board, isCastleMove=True))


class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move():
    # Map keys to values
    # key : value
    ranksToRows = {'1': 7, '2': 6, '3': 5,
                   '4': 4, '5': 3, '6': 2, '7': 1, '8': 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {'a': 0, 'b': 1, 'c': 2,
                   'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, isEnpassantMove=False, isCastleMove=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        # pawn promotion
        self.isPawnPromotion = (self.pieceMoved == 'wp' and self.endRow == 0) or (
            self.pieceMoved == 'bp' and self.endRow == 7)
        self.castle = isCastleMove
        # en passant move
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.pieceCaptured = 'wp' if self.pieceMoved == 'bp' else 'bp'
            
        self.isCapture = self.pieceCaptured!='--'

        # castle move
        self.isCastleMove = isCastleMove

        self.moveID = self.startRow*1000+self.startCol*100+self.endRow*10+self.endCol

    ''' 
    Overriding the equals method
    '''

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol)+self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]
    
    #overriding str() function
    def __str__(self):
        #castle move
        if self.castle:
            return 'O-O' if self.endCol==6 else 'O-O-O'
        
        endSquare = self.getRankFile(self.endRow, self.endCol)
        # pawn moves
        if self.pieceMoved[1]=='p':
            if self.isCapture:
                return self.colsToFiles[self.startCol]+'x'+endSquare
            else:
                return endSquare

            #pawn promotions
        #two same pieces moving to same square
        # add + for check and # for checkmate
        
        #piece moves
        moveString = self.pieceMoved[1]
        if self.isCapture:
            moveString+='x'
        return moveString+ endSquare
            
