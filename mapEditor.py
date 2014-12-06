# mapEditor.py
# by David Simon (dasimon@andrew.cmu.edu)
# Dec 2014

# Based on Advance Wars (Intelligent Systems, Nintendo)

import pygame
from pygame.locals import *
from pygameBaseClass import PygameBaseClass
from map import *
from units import *
from battle import *

class Editor(PygameBaseClass):
    modes = ['Terrain', 'Objective', 'Unit']
    teams = ['Red', 'Blue', 'Green', 'Yellow', 'Empty']
    terrain = ['Sea', 'Plain', 'Road', 'Forest', 'Mountain', 'River', 'Bridge']
    objectives = ['HQ', 'City', 'Factory']
    units = [Infantry, RocketInf, APC, SmTank, LgTank, Artillery]
    unitNames = ['Infantry', 'RocketInf', 'APC',
                 'SmTank', 'LgTank', 'Artillery']

    def initGraphics(self):
        self.backgrounds = self.loadBackgrounds()
        self.camWidth = 16
        self.camHeight = 10
        self.camTop = 0
        self.camLeft = 0
        self.camBottom = 10
        self.camRight = 16
        self.screenTopLeft = (0, 128)
        self.loadCursor()
        self.font = pygame.font.SysFont('Arial', 32, True)

    def __init__(self, arg):
        if type(arg) == tuple:
            row, cols = arg
            self.initFunds = 0
            self.map = Map(arg)
            self.unitList = []
            self.fileName = 'Untitled'
        else:
            self.fileName = arg[5:len(arg)-4]
            self.loadFile(arg)
        self.rows, self.cols = self.map.rows, self.map.cols
        screenSize = (self.cols * Tile.size, self.rows* Tile.size)
        self.screen = pygame.Surface(screenSize)
        self.cursorCoords = (0, 0)
        self.unitSpace = self.getUnitSpace()

    def getUnitSpace(self):
        """Create an empty 2D list the size of the map"""
        contents = []
        for row in xrange(self.rows):
            contents += [[None] * self.cols]
        return contents

    def placeInitialUnits(self):
        """Add the initial units to the unit space"""
        for item in self.unitList:
            teamNum, typeNum, coords = item
            type = Editor.units[typeNum-1]
            unit = type(teamNum)
            row, col = coords
            self.unitSpace[row][col] = unit
            self.redrawMapTile(coords)

    def redrawMapTile(self, coords):
        """Redraw the tile at the given coords"""
        row, col = coords
        left, top = col * Tile.size, row * Tile.size
        width = height = Tile.size
        self.drawMap(pygame.Rect(left, top, width, height))
        self.drawUnit(coords)
        if coords == self.cursorCoords:
            self.drawCursor(coords)

    def drawMap(self, boundingBox=None):
        """Draw the game map to the screen. If a boundingBox rect is given,
        only draw that portion of the map. Otherwise, draw the entire map."""
        if boundingBox == None:
            self.screen.blit(self.map.image, (0,0))
        else:
            self.screen.blit(self.map.image, boundingBox, area=boundingBox)

    def drawUnit(self, coords):
        """Draw a single unit at the specified unit space coords"""
        row, col = coords
        unit = self.unitSpace[row][col]
        if unit != None:
            drawCoords = (col*Tile.size, row*Tile.size)
            self.screen.blit(unit.image, drawCoords)

    def drawCursor(self, coords):
        """Draws a white rectangle"""
        row, col = coords
        top, left = row * Tile.size, col * Tile.size
        self.screen.blit(self.cursor, (left, top))

    @staticmethod
    def loadUnits(unitString):
        if len(unitString) == 0: return []
        units = []
        unitIdentifiers = unitString.splitlines()
        for i in xrange(len(unitIdentifiers)):
            thisUnitStr = unitIdentifiers[i]
            thisUnitList = thisUnitStr.split()
            team = int(thisUnitList[0])
            type = int(thisUnitList[1])
            rowAndCol = thisUnitList[2].split(',')
            coords = (int(rowAndCol[0]), int(rowAndCol[1]))
            units.append((team, type, coords))
        return units

    def loadFile(self, path):
        with open(path, "rt") as input:
            save = input.read()
        saveContents = save.split('\n*\n')
        mapString = saveContents[0]
        self.initFunds = int(saveContents[2])
        unitString = saveContents[3]
        self.map = Map(mapString)
        self.unitList = self.loadUnits(unitString)

    def loadBackgrounds(self):
        backgrounds = []
        for team in self.teams:
            if team == 'Empty':
                team = 'Red'
            filename = team + 'Background.png'
            path = os.path.join('backgrounds', filename)
            image = pygame.image.load(path)
            backgrounds.append(image)
        return backgrounds

    def placeCursor(self, coords):
        """Move the cursor to a new location, redrawing the old and new
        locations"""
        oldRow, oldCol = self.cursorCoords
        self.cursorCoords = coords
        self.redrawMapTile((oldRow, oldCol))
        self.redrawMapTile(self.cursorCoords)

    def loadCursor(self):
        """Create a white overlay, one tile in size, and store it in
        self.cursor"""
        self.cursor = pygame.Surface((Tile.size, Tile.size))
        color = pygame.Color('White')
        rect = pygame.Rect(0, 0, Tile.size, Tile.size)
        pygame.draw.rect(self.cursor, color, rect)
        self.cursor.set_alpha(128)

    def beginMusic(self):
        pygame.mixer.music.fadeout(1000)
        musicpath = os.path.join('audio', 'editor.ogg')
        pygame.mixer.music.load(musicpath)
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)

    def initGame(self):
        self.modeIndex = 0
        self.teamIndex = 0
        self.typeIndex = 0
        self.nameEntry = False
        self.beginMusic()
        self.drawMap()
        self.placeCursor((0, 0))
        self.placeInitialUnits()
        self.redrawAll()

    def drawScreen(self):
        displayTopLeft = (self.camLeft * Tile.size, self.camTop * Tile.size)
        displayDimensions = (self.camWidth * Tile.size,
                             self.camHeight * Tile.size)
        boundingBox = Rect(displayTopLeft, displayDimensions)
        self.display.blit(self.screen, self.screenTopLeft, area=boundingBox)
        pygame.display.flip()

    def adjustCam(self):
        row, col = self.cursorCoords
        if col < self.camLeft:
            self.camLeft -= 1
            self.camRight -= 1
        elif col >= self.camRight:
            self.camLeft += 1
            self.camRight += 1
        if row < self.camTop:
            self.camTop -= 1
            self.camBottom -= 1
        elif row >= self.camBottom:
            self.camTop += 1
            self.camBottom += 1

    def moveCursor(self, dir):
        """Handle motion of the cursor by the arrow keys"""
        oldRow, oldCol = self.cursorCoords
        newRow, newCol = None, None
        # get new Coords
        if dir == 'left':
            newRow, newCol = oldRow, oldCol - 1
        elif dir == 'right':
            newRow, newCol = oldRow, oldCol + 1
        elif dir == 'up':
            newRow, newCol = oldRow - 1, oldCol
        elif dir == 'down':
            newRow, newCol = oldRow + 1, oldCol
        # if new coords are legal, change cursorCoords
        if 0 <= newRow < self.rows and 0 <= newCol < self.cols:
            coords = (newRow, newCol)
            self.placeCursor(coords)
            self.adjustCam()

    def name(self, keyName):
        if keyName == 'return':
            self.nameEntry = False
        elif keyName in 'abcdefghijklmnopqrstuvwxyz1234567890':
            self.fileName += keyName
            self.redrawAll()
        elif keyName == 'space':
            self.fileName += ' '
            self.redrawAll()
        elif keyName == 'backspace':
            self.fileName = self.fileName[:len(self.fileName)-1]
            self.redrawAll()

    def onKeyDown(self, event):
        keyName = pygame.key.name(event.key)
        if keyName == 'escape':
            self.quit()
        elif self.nameEntry:
            self.name(keyName)
        elif keyName in ['left', 'right', 'up', 'down']:
            self.moveCursor(keyName)
            self.redrawAll()
        elif keyName in ['q', 'a']:
            self.changeTeam(keyName)
            self.redrawAll()
        elif keyName in ['w', 's']:
            self.changeMode(keyName)
            self.redrawAll()
        elif keyName in ['e', 'd']:
            self.changeFunds(keyName)
            self.redrawAll()
        elif keyName in ['r', 'f']:
            self.changeIndex(keyName)
            self.redrawAll()
        elif keyName == 'z':
            self.changeMap()
            self.redrawAll()
        elif keyName == 'x':
            self.delete()
            self.redrawAll()
        elif keyName == 'space':
            self.save()
            self.quit()
        elif keyName == 'n':
            self.nameEntry = True

    def getSaveString(self):
        mapStr = ''
        unitStr = ''
        numPlayers = 0
        for row in xrange(self.rows):
            if row != 0: mapStr += '\n'
            for col in xrange(self.cols):
                tile = self.map.map[row][col]
                unit = self.unitSpace[row][col]
                if isinstance(tile, Objective):
                    mapStr += '%d%d ' % (tile.teamNum, tile.typeNum)
                    if tile.typeNum == 0:
                        numPlayers += 1
                else:
                    mapStr += '%d  ' % tile.terrainType
                if unit != None:
                    if len(unitStr) != 0: unitStr += '\n'
                    typeNum = self.unitNames.index(unit.type) + 1
                    unitStr += '%d %d %d,%d' % (unit.teamNum, typeNum,
                                                row, col)
        saveStr = '%s\n*\n%d\n*\n%d\n*\n%s' % (mapStr, numPlayers,
                                               self.initFunds, unitStr)
        return saveStr

    def save(self):
        saveStr = self.getSaveString()
        path = os.path.join('maps', self.fileName + '.tpm')
        with open(path, 'wt') as saveFile:
            saveFile.write(saveStr)


    def findOldHQ(self):
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                tile = self.map.map[row][col]
                if (isinstance(tile, Objective) and tile.typeNum == 0 and
                    tile.teamNum == self.teamIndex):
                    return (row, col)

    def changeMap(self):
        if self.modeIndex == 0:
            self.map.changeTile(self.typeIndex, self.cursorCoords)
            self.redrawMapTile(self.cursorCoords)
            self.redrawSurroundingTiles(self.cursorCoords)
        elif self.modeIndex == 1:
            if self.teamIndex != 4:
                if self.typeIndex == 0:
                    oldHQ = self.findOldHQ()
                else: oldHQ = None
                self.map.changeTile((self.teamIndex, self.typeIndex),
                                    self.cursorCoords)
                self.redrawMapTile(self.cursorCoords)
                self.redrawSurroundingTiles(self.cursorCoords)
                if oldHQ != None:
                    self.redrawMapTile(oldHQ)
                    self.redrawSurroundingTiles(oldHQ)
            else:
                self.map.changeTile((self.teamIndex, self.typeIndex+1),
                                    self.cursorCoords)
                self.redrawMapTile(self.cursorCoords)
                self.redrawSurroundingTiles(self.cursorCoords)
        elif self.modeIndex == 2 and self.teamIndex != 4:
            row, col = self.cursorCoords
            unitType = self.units[self.typeIndex]
            self.unitSpace[row][col] = unitType(self.teamIndex)
            self.redrawMapTile(self.cursorCoords)

    def changeIndex(self, keyName):
        if keyName == 'r':
            self.typeIndex -= 1
        elif keyName == 'f':
            self.typeIndex += 1

        mode = self.modes[self.modeIndex]
        if mode == 'Unit':
            if self.teamIndex != 4:
                possible = len(self.units)
            else:
                possible = 1
        elif mode == 'Terrain':
            possible = len(self.terrain)
        elif mode == 'Objective':
            if self.teamIndex == 4:
                possible = len(self.objectives) - 1
            else:
                possible = len(self.objectives)
        self.typeIndex %= possible

    def redrawSurroundingTiles(self, coords):
        dirs = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        cRow, cCol = coords
        for (dRow, dCol) in dirs:
            nRow, nCol = newCoords = cRow + dRow, cCol + dCol
            if 0 <= nRow < self.rows and 0 <= nCol < self.cols:
                self.redrawMapTile(newCoords)

    def delete(self):
        mode = self.modes[self.modeIndex]
        row, col = coords = self.cursorCoords
        if mode == 'Terrain' or mode == 'Objective':
            self.map.changeTile(Tile.defaultType, coords)
            self.redrawMapTile(self.cursorCoords)
            self.redrawSurroundingTiles(self.cursorCoords)
        elif mode == 'Unit':
            self.unitSpace[row][col] = None
            self.redrawMapTile(self.cursorCoords)

    def changeFunds(self, keyName):
        if keyName == 'e':
            self.initFunds += 1000
        elif keyName == 'd' and self.initFunds > 0:
            self.initFunds -= 1000

    def changeMode(self, keyName):
        if keyName == 'w':
            self.modeIndex -= 1
        elif keyName == 's':
            self.modeIndex += 1
        self.typeIndex = 0
        self.modeIndex %= len(self.modes)

    def changeTeam(self, keyName):
        if keyName == 'q':
            self.teamIndex -= 1
        elif keyName == 'a':
            self.teamIndex += 1
        self.typeIndex = 0
        self.teamIndex %= len(self.teams)

    def drawBackground(self):
        backgroundIndex = self.teamIndex
        background = self.backgrounds[backgroundIndex]
        self.display.blit(background, (0,0))

    def drawFileName(self):
        text = '(n) File: %s' % self.fileName
        surface = self.font.render(text, 1, (0, 0, 0))
        self.display.blit(surface, (32, 48))

    def drawTeam(self):
        text = '(q/a) Team: %s' % self.teams[self.teamIndex]
        surface = self.font.render(text, 1, (0, 0, 0))
        self.display.blit(surface, (352, 48))

    def drawMode(self):
        text = '(w/s) Mode: %s' % self.modes[self.modeIndex]
        surface = self.font.render(text, 1, (0, 0, 0))
        self.display.blit(surface, (640, 48))

    def drawFunds(self):
        text = '(e/d) Funds: %d' % self.initFunds
        surface = self.font.render(text, 1, (0, 0, 0))
        self.display.blit(surface, (960, 48))

    def drawPossible(self):
        mode = self.modes[self.modeIndex]
        left, top = 1048, 144
        if mode == 'Unit':
            if self.teamIndex != 4:
                possible = [unit.__name__ for unit in self.units]
            else:
                possible = []
        elif mode == 'Terrain':
            possible = self.terrain
        elif mode == 'Objective':
            if self.teamIndex == 4:
                possible = self.objectives[1:]
            else:
                possible = self.objectives
        text = self.font.render('(r/f) Types:', 1, (0, 0, 0))
        self.display.blit(text, (left, top))
        for i in xrange(len(possible)):
            typeName = possible[i]
            if i == self.typeIndex:
                color = (0, 0, 255)
            else:
                color = (0, 0, 0)
            text = self.font.render(typeName, 1, color)
            nameTop = top + 32 + (i * 32)
            self.display.blit(text, (left, nameTop))

    def drawInstructions(self):
        left, top = 1048, 576
        instructions = ['Move with', 'Arrow Keys', '(z) Edit Map',
                '(x) Delete', '(space) Save']
        for i in xrange(len(instructions)):
            text = instructions[i]
            surface = self.font.render(text, 1, (0, 0, 0))
            self.display.blit(surface, (left, top + i * 32))

    def redrawAll(self):
        self.drawScreen()
        self.drawBackground()
        self.drawFileName()
        self.drawTeam()
        self.drawMode()
        self.drawFunds()
        self.drawPossible()
        self.drawInstructions()
        pygame.display.flip()


