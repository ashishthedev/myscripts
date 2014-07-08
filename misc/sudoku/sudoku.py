############################################################
## Intent: To feed a sudoku puzzle and solve it.
##
## 2013-04-08 Mon 10:50 AM
##
## Author: Ashish Anand
############################################################

from Util.Admin import ShootMailToAdmin
from Util.Misc import PrintInBox

import os
F = os.path.join("B:\\Desktop", "status.txt")
f = open(F, "w")
#http://www.sudoku.ws/extreme-1.htm
EXTREME_BOARD = """
009 748 000
700 602 000
020 109 000

007 986 241
264 317 598
198 524 367

000 863 020
000 491 006
000 275 900
""".replace(' ', '').replace('\n', '')

EXTREME_BOARD_HT = """
000000395
500300100
000074000
004005200
032407580
005600700
000860000
008003007
163000000
""".replace(' ', '').replace('\n', '')

EASY_BOARD = """
019748632
783652419
426139875
357986241
264317598
198524367
975863124
832491756
641275980
""".replace(' ', '').replace('\n', '')

STARTING_BOARD="""
7 9 6   0 0 0   3 0 1
0 5 0   0 0 6   9 0 0
8 2 4   1 3 9   5 7 6

1 7 0   9 6 5   0 0 2
2 3 5   4 1 8   7 6 9
4 6 8   7 2 3   1 0 0

6 1 0   5 9 0   2 3 8
5 0 2   3 0 0   0 0 0
3 0 9   0 0 0   0 5 4
""".replace(' ', '').replace('\n', '')

STARTING_BOARD="""
3 0 0   0 2 8   1 4 0
0 0 8   5 1 0   0 3 2
2 1 0   0 3 6   5 8 9

0 2 3   0 7 1   0 6 5
6 0 0   2 0 5   0 7 3
7 0 0   3 6 0   2 1 0

1 0 2   6 5 3   0 9 0
0 0 0   0 0 2   3 5 1
5 3 0   1 4 0   0 2 0
""".replace(' ', '').replace('\n', '')

class Board():
    def __init__(self, strRepr):
        assert len(strRepr) == 81
        self.board = strRepr

    def IsEmpty(self, x, y):
        return self.Get(x, y) == "0"

    def Get(self, x, y):
        return self.board[(x) * 9 + y]

    def GetRow(self, i):
        assert i < 9 and i >= 0
        res = ""
        for k in range(9):
            res += self.Get(i, k)
        return res

    def GetCol(self, i):
        assert i < 9 and i >= 0
        res = ""
        for k in range(9):
            res += self.Get(k, i)
        return res

    def GetBox(self, i):
        res = ""
        r = (i / 3) * 3
        c = (i % 3) * 3
        res += self.Get(r + 0, c + 0)
        res += self.Get(r + 0, c + 1)
        res += self.Get(r + 0, c + 2)
        res += self.Get(r + 1, c + 0)
        res += self.Get(r + 1, c + 1)
        res += self.Get(r + 1, c + 2)
        res += self.Get(r + 2, c + 0)
        res += self.Get(r + 2, c + 1)
        res += self.Get(r + 2, c + 2)
        return res

    def Set(self, x, y, val):
        assert int(val)>=0 and int(val)<10, val + "should be between 0-9"
        pos = x*9+y
        self.board = self.board[0:pos] + str(val) + self.board[pos+1:]
        return

    def Deduce(self):
        """
        Tries to find out if you can deduce anything as it is before applying brute force.
        If yes then returns True with the output, if no, then returns False
        """
        for r in range(9):
            for c in range(9):
                if not self.IsEmpty(r, c): continue
                validValuesForThisColumn = ""
                for val in range(1, 10):
                    if self.CanIPlaceThisOverThere(r, c, val):
                        validValuesForThisColumn += str(val)
                if len(validValuesForThisColumn) == 1:
                    return (True, r, c, validValuesForThisColumn)
        return (False, 0, 0, 0)

    def IsValid(self):
        for i in range(9):
            row = self.GetRow(i)
            col = self.GetCol(i)
            box = self.GetBox(i)
            for c in range(1, 10):
                if row.count(str(c)) > 1: return False
                if col.count(str(c)) > 1: return False
                if box.count(str(c)) > 1: return False
        return True

    def CanIPlaceThisOverThere(self, x, y, val):
        assert int(val) < 10 and int(val)>0
        prevVal = self.Get(x, y)
        self.Set(x, y, val)
        retVal = False
        if self.IsValid():
            retVal = True
        self.Set(x, y, prevVal)
        return retVal

    def IsComplete(self):
        """ If it is completely filled and valid then it is solved"""
        for r in range(9):
            for c in range(9):
                if self.IsEmpty(r, c):
                    return False
        return self.IsValid()

    def GetAsStr(self):
        newStr = ""
        for r in range(9):
            for c in range(9):
                newStr += self.Get(r, c) + " "
                if c%3 == 2:
                    newStr += "  "
            if r%3 == 2:
                newStr += "\n"
            newStr += "\n"
        return newStr


def ApplyBruteForce(ib):

    #import random; print("."*random.randint(1,10))
    if ib.IsComplete():
        PrintInBox("Solved. Sending mail to indicate completion")
        ShootMailToAdmin("solved", ib.GetAsStr())
        print(ib.GetAsStr())
        return True

    (canDeduce, x, y, val) = ib.Deduce()
    if canDeduce:
        #If you can deduce something, make that move and apply the brute force again.
        ib.Set(x, y, val)
        return ApplyBruteForce(ib)

    if not canDeduce: #If you cannot deduce, then apply the brute force
        for r in range(9):
            for c in range(9):
                if ib.IsEmpty(r, c):
                    for val in range(1, 10):
                        newBoard = Board(ib.board)
                        newBoard.Set(r, c, val)
                        if newBoard.IsValid():
                            solved = ApplyBruteForce(newBoard)
                            if solved: return solved
                            else: pass #keep running things
    return False

def main():
    #ib = Board(STARTING_BOARD)
    #ib = Board(EASY_BOARD)
    ib = Board(EXTREME_BOARD_HT)
    #ib = Board(EXTREME_BOARD) #TODO: Solve this internet puzzle.
    assert (ib.IsValid())
    if raw_input("There are {} number of empty boxes. Start applying brute force?(y/n)".format(ib.board.count('0'))).lower() == 'y':
        ApplyBruteForce(ib)


if __name__ == '__main__':
    main()
