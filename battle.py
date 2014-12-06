# battle.py
# by David Simon (dasimon@andrew.cmu.edu)
# Dec 2014

# Based on Advance Wars (Intelligent Systems, Nintendo)

import copy
import random
import pygame
from pygame.locals import *
from pygameBaseClass import PygameBaseClass
from map import *
from units import *

class Team(object):
    colors = ["Red", "Blue", "Green", "Yellow"]
    def __init__(self, teamNumber, funds, cursorCoords, camRect):
        self.teamNumber = teamNumber
        self.funds = funds
        self.color = Team.colors[teamNumber]
        self.heldObjectives = []
        self.units = set()
        self.cursorCoords = cursorCoords
        self.camLeft = camRect[0]
        self.camTop = camRect[1]
        self.camRight = camRect[2]
        self.camBottom = camRect[3]
        self.hudImage = self.getHudImage()

    def getHudImage(self):
        filename = self.color + 'Background.png'
        path = os.path.join('backgrounds', filename)
        image = pygame.image.load(path)
        return image

class Battle(PygameBaseClass):
    """Main gametype"""

    shopTypes = {
        1: Infantry,
        2: RocketInf,
        3: APC,
        4: SmTank,
        5: LgTank,
        6: Artillery
    }
    shopCosts = {
        1: 1000,
        2: 3000,
        3: 4000,
        4: 7000,
        5: 16000,
        6: 6000
    }

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

    @staticmethod
    def fromFile(path):
        with open(path, "rt") as input:
            save = input.read()
        saveContents = save.split('\n*\n')
        mapString = saveContents[0]
        numPlayers = int(saveContents[1])
        initialFunds = int(saveContents[2])
        unitString = saveContents[3]
        map = Map(mapString)
        units = Battle.loadUnits(unitString)
        return Battle(map, numPlayers, initialFunds, units)

    ##################################################################
    # Game setup
    ##################################################################

    def __init__(self, map, numPlayers, initialFunds=5000, initialUnits=[]):
        # super(Battle, self).__init__('Battle')
        self.map = map
        self.rows, self.cols = map.rows, map.cols
        self.unitSpace = self.getUnitSpace()
        self.numPlayers = numPlayers
        self.initialFunds = initialFunds
        self.teams = self.createTeams()
        self.placeInitialUnits(initialUnits)

    def initGraphics(self):
        self.camWidth = 16
        self.camHeight = 10
        self.camLeft, self.camTop = (0, 0)
        self.screenTopLeft = (0, 128)
        self.screenDisplaySize = (1024, 640)
        self.screenSize = (self.map.cols*Tile.size, self.map.rows*Tile.size)
        self.screen = pygame.Surface(self.screenSize)
        self.camTop = 0
        self.camLeft = 0
        self.camBottom = 10
        self.camRight = 16

    def getUnitSpace(self):
        """Create an empty 2D list the size of the map"""
        contents = []
        for row in xrange(self.rows):
            contents += [[None] * self.cols]
        return contents

    def getHQCoords(self, teamNum):
        map = self.map.map
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                tile = map[row][col]
                if (isinstance(tile, Objective) and
                    tile.typeNum == 0 and
                    tile.teamNum == teamNum):
                    return (row, col)

    def getCamRect(self, hqCoords):
        row, col = hqCoords
        camWidth = 16
        camHeight = 10
        camRight = col + camWidth/2
        camLeft = camRight - camWidth
        camBottom = row + camHeight/2
        camTop = camBottom - camHeight
        while camLeft < 0:
            camLeft += 1
            camRight += 1
        while camRight > self.cols:
            camLeft -= 1
            camRight -= 1
        while camTop < 0:
            camTop += 1
            camBottom += 1
        while camBottom > self.rows:
            camTop -= 1
            camBottom -= 1
        camRect = [camLeft, camTop, camRight, camBottom]
        return camRect

    def createTeams(self):
        """Create the appropriate number of teams, each with the initial
        amount of funds"""
        teams = []
        for teamNumber in xrange(self.numPlayers):
            hqCoords = self.getHQCoords(teamNumber)
            camRect = self.getCamRect(hqCoords)
            teams.append(Team(teamNumber, self.initialFunds, hqCoords, camRect))
        return teams

    def placeInitialUnits(self, initialUnits):
        """Add the initial units to the unit space"""
        for item in initialUnits:
            teamNum, typeNum, coords = item
            type = Battle.shopTypes[typeNum]
            team = self.teams[teamNum]
            row, col = coords
            unit = type(teamNum)
            self.unitSpace[row][col] = unit
            team.units.add(unit)

    def beginMusic(self):
        pygame.mixer.music.fadeout(1000)
        musicpath = os.path.join('audio', 'battle.ogg')
        pygame.mixer.music.load(musicpath)
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)

    def initGame(self):
        """Set up initial game conditions"""
        self.beginMusic()
        self.gameIsOver = False
        self.eliminatedPlayers = set()
        self.contextMenuIsOpen = False
        self.contextMenuOptions = [False, False]
        self.inAttackMode = False
        self.shopIsOpen = False
        self.shopCoords = None
        self.attackerCoords = None
        self.attackKey = '2'
        self.unitIsSelected = False
        self.captureKey = '3'
        self.getHeldObjectives()
        firstPlayer = random.randrange(self.numPlayers)
        self.playerIndex = firstPlayer
        self.activePlayer = self.teams[self.playerIndex]
        self.activeUnits = copy.copy(self.activePlayer.units)
        self.loadCursor()
        self.loadMovementOverlay()
        self.loadMovedMarker()
        self.loadTargetOverlay()
        self.movementRange = set()
        self.cursorCoords = (0, 0)
        self.targetCoords = None
        self.targets = []
        self.targetIndex = 0
        self.drawMap()
        self.drawAllUnits()
        self.beginTurn()

    def getHeldObjectives(self):
        """Add each objective to the heldObjectives list of the team that
        holds it"""
        map = self.map
        for row in xrange(map.rows):
            for col in xrange(map.cols):
                tile = self.map.map[row][col]
                if isinstance(tile, Objective) and tile.teamNum != 4:
                    holdingTeam = self.teams[tile.teamNum]
                    holdingTeam.heldObjectives.append(tile)

    def loadCursor(self):
        """Create a white overlay, one tile in size, and store it in
        self.cursor"""
        self.cursor = pygame.Surface((Tile.size, Tile.size))
        color = pygame.Color('White')
        rect = pygame.Rect(0, 0, Tile.size, Tile.size)
        pygame.draw.rect(self.cursor, color, rect)
        self.cursor.set_alpha(128)

    def loadMovementOverlay(self):
        """Create a green overlay, one tile in size, and store it in
        self.movementOverlay"""
        self.movementOverlay = pygame.Surface((Tile.size, Tile.size))
        color = pygame.Color('Green')
        rect = pygame.Rect(0, 0, Tile.size, Tile.size)
        pygame.draw.rect(self.movementOverlay, color, rect)
        self.movementOverlay.set_alpha(128)

    def loadMovedMarker(self):
        """Create a brown overlay, one tile in size, and store it in
        self.movedMarker"""
        self.movedMarker = pygame.Surface((Tile.size, Tile.size))
        color = pygame.Color('#804000')
        rect = pygame.Rect(0, 0, Tile.size, Tile.size)
        pygame.draw.rect(self.movedMarker, color, rect)
        self.movedMarker.set_alpha(128)

    def loadTargetOverlay(self):
        """Create a green overlay, one tile in size, and store it in
        self.targetOverlay"""
        self.targetOverlay = pygame.Surface((Tile.size, Tile.size))
        color = pygame.Color('Red')
        rect = pygame.Rect(0, 0, Tile.size, Tile.size)
        pygame.draw.rect(self.targetOverlay, color, rect)
        self.targetOverlay.set_alpha(128)

    ##################################################################
    # Gameplay methods
    ##################################################################

    def beginTurn(self):
        """Start the turn of the active player"""
        self.activePlayer = self.teams[self.playerIndex]
        additionalFundsPerBuilding = 1000
        newFunds = (additionalFundsPerBuilding *
                     len(self.activePlayer.heldObjectives))
        self.activePlayer.funds += newFunds
        self.activeUnits = copy.copy(self.activePlayer.units)
        self.placeCursor(self.activePlayer.cursorCoords)
        self.camLeft = self.activePlayer.camLeft
        self.camRight = self.activePlayer.camRight
        self.camTop = self.activePlayer.camTop
        self.camBottom = self.activePlayer.camBottom
        self.selection = None
        self.clearMovementRange()
        self.restoreUnitHealth()
        self.drawAllUnits()
        self.drawScreen()
        self.drawHUD()

    def placeCursor(self, coords):
        """Move the cursor to a new location, redrawing the old and new
        locations"""
        oldRow, oldCol = self.cursorCoords
        self.cursorCoords = coords
        self.redrawMapTile((oldRow, oldCol))
        self.redrawMapTile(self.cursorCoords)

    def placeUnit(self, team, type, coords):
        """Place and draw the given unit in the given tile"""
        row, col = coords
        teamColor = self.teams[team].color
        self.unitSpace[row][col] = type(team)
        self.drawUnit(coords)

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
        self.drawScreen()

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

    def getNextTiles(self, map, unit, coords):
        """Return a list of the tiles adjacent to (row, col), sorted by
        movement cost for the given unit"""
        row, col = coords
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        nextTiles = []
        for (dRow, dCol) in directions:
            nextRow = row + dRow
            nextCol = col + dCol
            nextTiles.append((nextRow, nextCol))
        return nextTiles

    def isBlocked(self, coords):
        """Return true if (row, col) is occupied by an enemy team"""
        row, col = coords
        unit = self.unitSpace[row][col]
        activeTeam = self.activePlayer.color
        return (unit != None) and (unit.team != activeTeam)

    def movementRangeHelperFunction(self, map, unit, coords, movementPoints):
        """Do a weighted floodfill method to populate the movement range"""
        row, col = coords
        if not (0 <= row < self.rows and 0 <= col < self.cols): return
        terrainType = map[row][col].terrainType
        movementCost = unit.movementCost[terrainType]
        pointsAfterMove = movementPoints - movementCost
        if (pointsAfterMove > 0 and movementCost != -1 and
            not self.isBlocked(coords)):
            self.movementRange.add(coords)
            for newCoords in self.getNextTiles(map, unit, coords):
                self.movementRangeHelperFunction(map, unit,
                                                 newCoords, pointsAfterMove)

    def getMovementRange(self):
        """Calculate movement range from the current selection"""
        map = self.map.map
        row, col = self.selection
        unit = self.unitSpace[row][col]
        movementPoints = unit.movementPoints
        self.movementRange.add(self.selection)
        for newCoords in self.getNextTiles(map, unit, self.selection):
                    self.movementRangeHelperFunction(map, unit,
                                                     newCoords,
                                                     movementPoints)
        self.drawMovementRange()

    def clearMovementRange(self):
        """Clear the movement range and redrawing all of the tiles"""
        oldMovementRange = self.movementRange
        self.movementRange = set()
        for tile in oldMovementRange:
            self.redrawMapTile(tile)
        self.drawScreen()

    def checkArtilleryRange(self, unit, coords):
        maxDistance = unit.artilleryMaxRange
        minDistance = unit.artilleryMinRange
        cRow, cCol = coords
        for row in xrange(cRow - maxDistance, cRow + maxDistance + 1):
            for col in xrange(cCol - maxDistance, cCol + maxDistance + 1):
                taxicabDistance = abs(row - cRow) + abs(col - cCol)
                if ((0 <= row < self.rows) and (0 <= col < self.cols) and
                    self.isBlocked((row, col)) and
                    (minDistance <= taxicabDistance <= maxDistance)):
                    return True
        return False

    def checkAdjacent(self, coords):
        cRow, cCol = coords
        adjacentDir = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for (dRow, dCol) in adjacentDir:
            newRow, newCol = cRow + dRow, cCol + dCol
            if ((0 <= newRow <= self.rows and 0 <= newCol < self.cols) and
                self.isBlocked((newRow, newCol))):
                return True
        return False

    def canAttack(self, unit, coords, distanceMoved):
        if unit.isArtilleryUnit and distanceMoved == 0:
            return self.checkArtilleryRange(unit, coords)
        elif not unit.isArtilleryUnit:
            return self.checkAdjacent(coords)
        else:
            return False

    def canCapture(self, unit, coords):
        row, col = coords
        tile = self.map.map[row][col]
        return (unit.canCapture and isinstance(tile, Objective) and
                (unit.team != tile.team))

    def openContextMenu(self, unit, coords, distanceMoved):
        self.contextMenuIsOpen = True
        self.contextMenuOptions = [False, False]
        self.attackKey = None
        self.captureKey = None
        key = 1
        if self.canAttack(unit, coords, distanceMoved):
            key += 1
            self.attackKey = str(key)
            self.contextMenuOptions[0] = True
        if self.canCapture(unit, coords):
            key += 1
            self.captureKey = str(key)
            self.contextMenuOptions[1] = True
        self.drawHUD()

    def moveUnit(self, old, new):
        """Move the unit from one tile to another"""
        oldRow, oldCol = old
        newRow, newCol = new
        if self.unitSpace[newRow][newCol] == None:
            unit = self.unitSpace[oldRow][oldCol]
            self.unitSpace[newRow][newCol] = unit
            self.unitSpace[oldRow][oldCol] = None
            self.redrawMapTile(old)
            self.redrawMapTile(new)
        self.selection = None
        self.clearMovementRange()

    def updateSelection(self):
        """Handle the changing selection"""
        row, col = self.cursorCoords
        if self.selection == None:
            # get the selection and movement range
            row, col = self.cursorCoords
            unit = self.unitSpace[row][col]
            tile = self.map.map[row][col]
            if ((unit != None) and
                (unit.team == self.activePlayer.color) and
                (unit in self.activeUnits)):
                self.unitIsSelected = True
                self.selection = self.cursorCoords
                self.getMovementRange()
            elif ((unit == None) and isinstance(tile, Objective) and
                  (tile.team == self.activePlayer.color) and
                  (tile.type == 'Factory')):
                self.shopIsOpen = True
                self.shopCoords = self.cursorCoords
                self.drawScreen()
        elif (self.cursorCoords in self.movementRange and
              (self.unitSpace[row][col] == None or
               self.selection == self.cursorCoords)):
            self.oldCoords = oldRow, oldCol = self.selection
            self.newCoords = newRow, newCol = self.cursorCoords
            self.moveUnit(self.selection, self.cursorCoords)
            taxicabDistance = abs(newRow - oldRow) + abs(newCol - oldCol)
            unit = self.unitSpace[newRow][newCol]
            self.openContextMenu(unit, self.newCoords, taxicabDistance)
        else:
            self.clearSelection

    def clearSelection(self):
        """Clear the selection and the movement range"""
        self.unitIsSelected = False
        self.selection = None
        self.clearMovementRange()

    def restoreObjectives(self):
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                unit = self.unitSpace[row][col]
                objective = self.map.map[row][col]
                if (isinstance(objective, Objective) and
                    (unit == None or unit.team == objective.team)):
                    objective.health = Objective.baseHealth

    def restoreUnitHealth(self):
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                unit = self.unitSpace[row][col]
                objective = self.map.map[row][col]
                if ((unit != None) and isinstance(objective, Objective) and
                    (unit.team == objective.team) and
                    (unit.team == self.activePlayer.color)):
                    unit.health += 50
                    if unit.health > 100:
                        unit.health = 100

    def endTurn(self):
        """Store the current player's cursor position and begin the next
        player's turn"""
        self.restoreObjectives()
        for unit in self.activePlayer.units:
            unit.hasMoved = False
        self.activePlayer.cursorCoords = self.cursorCoords
        self.activePlayer.camLeft = self.camLeft
        self.activePlayer.camRight = self.camRight
        self.activePlayer.camTop = self.camTop
        self.activePlayer.camBottom = self.camBottom
        self.playerIndex += 1
        while self.playerIndex in self.eliminatedPlayers:
            self.playerIndex += 1
        self.playerIndex %= self.numPlayers
        self.beginTurn()

    def wait(self):
        row, col = self.newCoords
        unit = self.unitSpace[row][col]
        unit.hasMoved = True
        self.unitIsSelected = False
        self.activeUnits.remove(unit)
        self.contextMenuIsOpen = False
        self.redrawMapTile(self.newCoords)
        self.drawScreen()

    def revertMove(self):
        self.moveUnit(self.newCoords, self.oldCoords)
        self.contextMenuIsOpen = False
        self.unitIsSelected = False
        self.drawHUD()

    def endGame(self):
        self.gameIsOver = True
        self.winner = None
        for team in self.teams:
            if team.teamNumber not in self.eliminatedPlayers:
                self.winner = team
        self.drawScreen()

    def removeTeam(self, teamNum):
        self.eliminatedPlayers.add(teamNum)
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                unit = self.unitSpace[row][col]
                tile = self.map.map[row][col]
                if unit != None and unit.teamNum == teamNum:
                    self.unitSpace[row][col] = None
                if isinstance(tile, Objective) and tile.teamNum == teamNum:
                    typeNum = tile.typeNum
                    if typeNum == 0: typeNum = 1 # replace HQ with a city
                    self.map.map[row][col] = Objective((4, typeNum))
        if self.numPlayers - len(self.eliminatedPlayers) == 1:
            self.endGame()
        self.map.refreshImage()
        self.drawMap()
        self.drawAllUnits()
        self.drawScreen()

    def capture(self):
        row, col = self.newCoords
        objective = self.map.map[row][col]
        unit = self.unitSpace[row][col]
        objective.health -= (unit.health / 10)
        if objective.health <= 0:
            oldTeam = objective.teamNum
            if oldTeam != 4:
                self.teams[oldTeam].heldObjectives.remove(objective)
            team = unit.teamNum
            type = objective.typeNum
            if type == 0:
                self.removeTeam(oldTeam)
                type = 1 # don't allow a team to gain more than one HQ
            newObjective = Objective((team, type))
            self.map.map[row][col] = newObjective
            self.activePlayer.heldObjectives.append(newObjective)
            self.map.refreshImage()
            self.redrawMapTile((row, col))
            self.redrawMapTile((row-1, col))
            self.drawScreen()
        self.wait()

    def moveTarget(self):
        oldCoords = None
        newCoords = self.targets[self.targetIndex]
        if self.targetCoords != None:
            oldCoords = self.targetCoords
        self.targetCoords = newCoords
        if oldCoords != None:
            self.redrawMapTile(oldCoords)
        self.redrawMapTile(newCoords)
        self.drawScreen()

    def getArtilleryTargets(self):
        cRow, cCol = self.attackerCoords
        unit = self.unitSpace[cRow][cCol]
        maxDistance = unit.artilleryMaxRange
        minDistance = unit.artilleryMinRange
        for row in xrange(cRow - maxDistance, cRow + maxDistance + 1):
            for col in xrange(cCol - maxDistance, cCol + maxDistance + 1):
                taxicabDistance = abs(row - cRow) + abs(col - cCol)
                if ((0 <= row < self.rows) and (0 <= col < self.cols) and
                    self.isBlocked((row, col)) and
                    (minDistance <= taxicabDistance <= maxDistance)):
                    self.targets.append((row, col))

    def getTargets(self):
        cRow, cCol = self.attackerCoords
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        for (dRow, dCol) in directions:
            row = cRow + dRow
            col = cCol + dCol
            if ((0 <= row < self.rows) and (0 <= col < self.cols) and
                self.isBlocked((row, col))):
                self.targets.append((row, col))

    def removeUnit(self, coords):
        row, col = coords
        unit = self.unitSpace[row][col]
        team = self.teams[unit.teamNum]
        team.units.remove(unit)
        self.unitSpace[row][col] = None
        if len(team.units) == 0:
            self.removeTeam(unit.teamNum)

    def attack(self):
        atkRow, atkCol = self.attackerCoords
        defRow, defCol = self.targets[self.targetIndex]
        attacker = self.unitSpace[atkRow][atkCol]
        defender = self.unitSpace[defRow][defCol]
        atkEnv = self.map.defense[atkRow][atkCol]
        defEnv = self.map.defense[defRow][defCol]
        defender.health -= attacker.getAttackDamage(defender, defEnv)
        if defender.health <= 0:
            self.removeUnit((defRow, defCol))
        elif not attacker.isArtilleryUnit and not defender.isArtilleryUnit:
            attacker.health -= defender.getRetaliatoryDamage(attacker, atkEnv)
            if attacker.health <= 0:
                self.removeUnit((atkRow, atkCol))
        self.unitIsSelected = False
        self.contextMenuIsOpen = False
        if self.unitSpace[atkRow][atkCol] != None:
            self.wait()

    def contextMenu(self, keyName):
        if keyName == '1':
            self.wait()
        elif keyName == self.attackKey:
            self.enterAttackMode()
        elif keyName == self.captureKey:
            self.capture()
        elif keyName == 'x':
            self.revertMove()

    def enterAttackMode(self):
        self.inAttackMode = True
        row, col = self.attackerCoords = self.cursorCoords
        self.targets = []
        self.targetIndex = 0
        unit = self.unitSpace[row][col]
        if unit.isArtilleryUnit:
            self.getArtilleryTargets()
        else:
            self.getTargets()
        self.moveTarget()

    def attackMode(self, keyName):
        if keyName == 'right':
            self.targetIndex += 1
            self.targetIndex %= len(self.targets)
            self.moveTarget()
        elif keyName == 'left':
            self.targetIndex -= 1
            self.targetIndex %= len(self.targets)
            self.moveTarget()
        elif keyName == 'z':
            self.inAttackMode = False
            self.attack()
            self.redrawMapTile(self.attackerCoords)
            self.redrawMapTile(self.targetCoords)
            self.drawScreen()
        elif keyName == 'x':
            self.inAttackMode = False
            self.redrawMapTile(self.attackerCoords)
            self.redrawMapTile(self.targetCoords)
            self.drawScreen()

    def shop(self, keyName):
        if keyName == 'x':
            self.shopIsOpen = False
            self.drawScreen()
        elif keyName in '123456':
            num = int(keyName)
            cost = Battle.shopCosts[num]
            if cost <= self.activePlayer.funds:
                self.activePlayer.funds -= cost
                type = Battle.shopTypes[num]
                team = self.activePlayer.teamNumber
                self.placeUnit(team, type, self.shopCoords)
                row, col = self.shopCoords
                unit = self.unitSpace[row][col]
                self.activePlayer.units.add(unit)
                unit.hasMoved = True
                self.redrawMapTile(self.shopCoords)
                self.shopIsOpen = False
                self.drawScreen()

    def onKeyDown(self, event):
        """Handle keypresses"""
        keyName = pygame.key.name(event.key)
        if keyName == 'escape':
            self.quit()
        elif self.gameIsOver:
            self.quit()
        elif self.shopIsOpen:
            self.shop(keyName)
        elif self.inAttackMode:
            self.attackMode(keyName)
        elif self.contextMenuIsOpen:
            self.contextMenu(keyName)
        elif keyName in ['left', 'right', 'up', 'down']:
            self.moveCursor(keyName)
        elif keyName == 'z':
            self.updateSelection()
        elif keyName == 'x':
            self.clearSelection()
        elif keyName == 'space':
            self.endTurn()

    ##################################################################
    # Drawing to "screen" surface
    ##################################################################

    def redrawMapTile(self, coords):
        """Redraw the tile at the given coords"""
        row, col = coords
        left, top = col * Tile.size, row * Tile.size
        width = height = Tile.size
        self.drawMap(pygame.Rect(left, top, width, height))
        self.drawUnit(coords)
        if coords in self.movementRange:
            self.drawMovementOverlay(coords)
        if coords == self.cursorCoords:
            self.drawCursor(coords)
        if self.inAttackMode and coords == self.targetCoords:
            self.drawTargetOverlay(coords)

    def drawMap(self, boundingBox=None):
        """Draw the game map to the screen. If a boundingBox rect is given,
        only draw that portion of the map. Otherwise, draw the entire map."""
        if boundingBox == None:
            self.screen.blit(self.map.image, (0,0))
            self.drawScreen()
        else:
            self.screen.blit(self.map.image, boundingBox, area=boundingBox)

    def drawMovedMarker(self, coords):
        row, col = coords
        top, left = row * Tile.size, col * Tile.size
        self.screen.blit(self.movedMarker, (left, top))

    def drawUnit(self, coords):
        """Draw a single unit at the specified unit space coords"""
        row, col = coords
        unit = self.unitSpace[row][col]
        if unit != None:
            drawCoords = (col*Tile.size, row*Tile.size)
            self.screen.blit(unit.image, drawCoords)
            if unit.hasMoved:
                self.drawMovedMarker(coords)

    def drawAllUnits(self):
        """Draw all the units in the unit space"""
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                unit = self.unitSpace[row][col]
                if unit != None:
                    self.redrawMapTile((row,col))
        self.drawScreen()

    def drawCursor(self, coords):
        """Draws a white rectangle"""
        row, col = coords
        top, left = row * Tile.size, col * Tile.size
        self.screen.blit(self.cursor, (left, top))

    def drawMovementOverlay(self, coords):
        """Draw an overlay on the tile specified by the coords"""
        row, col = coords
        top, left = row * Tile.size, col * Tile.size
        self.screen.blit(self.movementOverlay, (left, top))

    def drawMovementRange(self):
        """Placeholder. draws a green rectangle"""
        for tile in self.movementRange:
            self.redrawMapTile(tile)
        self.drawScreen()

    def drawTargetOverlay(self, coords):
        row, col = coords
        top, left = row * Tile.size, col * Tile.size
        self.screen.blit(self.targetOverlay, (left, top))

    ##################################################################
    # Drawing to the screen
    ##################################################################

    def drawScreen(self):
        displayTopLeft = (self.camLeft * Tile.size, self.camTop * Tile.size)
        displayDimensions = (self.camWidth * Tile.size,
                             self.camHeight * Tile.size)
        boundingBox = Rect(displayTopLeft, displayDimensions)
        self.display.blit(self.screen, self.screenTopLeft, area=boundingBox)
        self.drawHUD()
        pygame.display.flip()

    def drawBackground(self):
        background = self.activePlayer.hudImage
        self.display.blit(background, (0, 0))

    def drawHUDTileImage(self, tile, coords):
        x, y = coords
        image = tile.staticImage
        self.display.blit(image, (x, y - tile.overflow))

    def drawHUDTileName(self, tile, coords):
        nameFont = pygame.font.SysFont('Arial', 24, True)
        nameText = tile.name
        name = nameFont.render(nameText, 1, (0, 0, 0))
        self.display.blit(name, coords)

    def drawHUDTileDef(self, tile, coords):
        defFont = pygame.font.SysFont('Arial', 18)
        defText = "Def: " + str(tile.defense)
        defSurf = defFont.render(defText, 1, (0, 0, 0))
        self.display.blit(defSurf, coords)

    def drawHUDObjHealth(self, tile, coords):
        healthFont = pygame.font.SysFont('Arial', 18)
        healthText = "HP: " + str(tile.health)
        health = healthFont.render(healthText, 1, (0, 0, 0))
        self.display.blit(health, coords)

    def drawTerrainInfo(self):
        left, top = 1024, 654
        row, col = self.cursorCoords
        tile = self.map.map[row][col]
        imageCoords = (left + 32 , top + 4)
        self.drawHUDTileImage(tile, imageCoords)
        nameCoords = (left + 112, top)
        self.drawHUDTileName(tile, nameCoords)
        defCoords = (left + 112, top + 28)
        self.drawHUDTileDef(tile, defCoords)
        if isinstance(tile, Objective):
            healthCoords = (left + 112, top + 48)
            self.drawHUDObjHealth(tile, healthCoords)

    def drawHUDUnitImage(self, unit, coords):
        image = unit.image
        self.display.blit(image, coords)

    def drawHUDUnitName(self, unit, coords):
        nameFont = pygame.font.SysFont('Arial', 24, True)
        nameText = unit.type
        name = nameFont.render(nameText, 1, (0, 0, 0))
        self.display.blit(name, coords)

    def drawHUDUnitAtk(self, unit, coords):
        atkFont = pygame.font.SysFont('Arial', 18)
        atkText = "Atk: " + str(unit.attack)
        atk = atkFont.render(atkText, 1, (0, 0, 0))
        self.display.blit(atk, coords)

    def drawHUDUnitDef(self, unit, coords):
        defFont = pygame.font.SysFont('Arial', 18)
        defText = "Def: " + str(unit.defense)
        defSurf = defFont.render(defText, 1, (0, 0, 0))
        self.display.blit(defSurf, coords)

    def drawHUDUnitHealth(self, unit, coords):
        healthFont = pygame.font.SysFont('Arial', 18)
        healthText = "HP: " + str(unit.health)
        health = healthFont.render(healthText, 1, (0, 0, 0))
        self.display.blit(health, coords)

    def drawUnitInfo(self):
        left, top = 1024, 512
        row, col = self.cursorCoords
        unit = self.unitSpace[row][col]
        if unit != None:
            imageCoords = (left + 32, top + 8)
            self.drawHUDUnitImage(unit, imageCoords)
            nameCoords = (left + 112, top)
            self.drawHUDUnitName(unit, nameCoords)
            atkCoords = (left + 112, top + 28)
            self.drawHUDUnitAtk(unit, atkCoords)
            defCoords = (left + 112, top + 48)
            self.drawHUDUnitDef(unit, defCoords)
            healthCoords = (left + 112, top + 68)
            self.drawHUDUnitHealth(unit, healthCoords)

    def drawHUDWait(self, coords):
        waitFont = pygame.font.SysFont('Arial', 24, True)
        waitText = "(1) to Wait"
        wait = waitFont.render(waitText, 1, (0, 0, 0))
        self.display.blit(wait, coords)

    def drawHUDAttack(self, (left, top), num):
        coords = (left, top + (24*(num-1)))
        attackFont = pygame.font.SysFont('Arial', 24, True)
        attackText = "(%d) to Attack" % num
        attack = attackFont.render(attackText, 1, (0, 0, 0))
        self.display.blit(attack, coords)

    def drawHUDCapture(self, (left, top), num):
        coords = (left, top + (24*(num-1)))
        captureFont = pygame.font.SysFont('Arial', 24, True)
        captureText = "(%d) to Capture" % num
        capture = captureFont.render(captureText, 1, (0, 0, 0))
        self.display.blit(capture, coords)

    def drawExitContextMenu(self, (left, top), num):
        coords = (left, top + (24*(num-1)))
        exitFont = pygame.font.SysFont('Arial', 24, True)
        exitText = "(x) to Undo Move"
        exit = exitFont.render(exitText, 1, (0, 0, 0))
        self.display.blit(exit, coords)

    def drawContextMenu(self):
        left, top = 1000, 144
        canAttack = self.contextMenuOptions[0]
        canCapture = self.contextMenuOptions[1]
        num = 1
        self.drawHUDWait((left + 48, top))
        if canAttack:
            num += 1
            self.drawHUDAttack((left + 48, top), num)
        if canCapture:
            num += 1
            self.drawHUDCapture((left + 48, top), num)
        num += 1
        self.drawExitContextMenu((left + 48, top), num)

    def drawAtkInstr(self, coords):
        left, top = coords
        instrFont = pygame.font.SysFont('Arial', 24, True)
        instrText1 = "Use left/right arrow"
        instrText2 = "keys to select target"
        instrText3 = "(z) Attack"
        instrText4 = "(x) Back"
        instr1 = instrFont.render(instrText1, 1, (0, 0, 0))
        instr2 = instrFont.render(instrText2, 1, (0, 0, 0))
        instr3 = instrFont.render(instrText3, 1, (0, 0, 0))
        instr4 = instrFont.render(instrText4, 1, (0, 0, 0))
        self.display.blit(instr1, (left + 48, top ))
        self.display.blit(instr2, (left + 48, top + 24))
        self.display.blit(instr3, (left + 48, top + 48))
        self.display.blit(instr4, (left + 48, top + 72))

    def drawTarget(self, coords):
        left, top = coords
        row, col = self.targetCoords
        unit = self.unitSpace[row][col]
        imageCoords = (left + 56, top + 8)
        self.drawHUDUnitImage(unit, imageCoords)
        nameCoords = (left + 136, top)
        self.drawHUDUnitName(unit, nameCoords)
        atkCoords = (left + 136, top + 28)
        self.drawHUDUnitAtk(unit, atkCoords)
        defCoords = (left + 136, top + 48)
        self.drawHUDUnitDef(unit, defCoords)
        healthCoords = (left + 136, top + 68)
        self.drawHUDUnitHealth(unit, healthCoords)

    def drawAttackInstructions(self):
        left, top = 1000, 144
        self.drawAtkInstr((left, top))
        self.drawTarget((left, top + 96))

    def drawTurnText(self, coords):
        turnFont = pygame.font.SysFont('Tahoma', 64, True)
        turnText = "%s's Turn" % self.activePlayer.color
        turn = turnFont.render(turnText, 1, (0, 0, 0))
        self.display.blit(turn, coords)

    def drawMoneyText(self, coords):
        left, top = coords
        moneyFont = pygame.font.SysFont('Arial', 24, True)
        moneyText1 = "Funds: $%d" % self.activePlayer.funds
        moneyText2 = "Buildings: %d" % len(self.activePlayer.heldObjectives)
        moneyText3 = "+$%d per Turn" % (1000 *
                                        len(self.activePlayer.heldObjectives))
        money1 = moneyFont.render(moneyText1, 1, (0, 0, 0))
        money2 = moneyFont.render(moneyText2, 1, (0, 0, 0))
        money3 = moneyFont.render(moneyText3, 1, (0, 0, 0))
        self.display.blit(money1, coords)
        self.display.blit(money2, (left, top + 24))
        self.display.blit(money3, (left, top + 48))

    def drawPlayerInfo(self):
        left, top = 0, 0
        self.drawTurnText((left + 48, top + 24))
        self.drawMoneyText((1024 + 48, top + 24))

    def drawHUDInstr(self):
        left, top = 1000, 144
        text1 = 'Arrow keys to move'
        text2 = '(z) to select unit'
        text3 = '(space) to end turn'
        textFont = pygame.font.SysFont('Arial', 24, True)
        t1 = textFont.render(text1, 1, (0, 0, 0))
        t2 = textFont.render(text2, 1, (0, 0, 0))
        t3 = textFont.render(text3, 1, (0, 0, 0))
        self.display.blit(t1, (left + 48, top))
        self.display.blit(t2, (left + 48, top + 24))
        self.display.blit(t3, (left + 48, top + 48))

    def drawMovementInstr(self):
        left, top = 1000, 144
        text1 = 'Arrow keys to move'
        text2 = '(z) to move unit'
        text3 = '(x) to undo'
        textFont = pygame.font.SysFont('Arial', 24, True)
        t1 = textFont.render(text1, 1, (0, 0, 0))
        t2 = textFont.render(text2, 1, (0, 0, 0))
        t3 = textFont.render(text3, 1, (0, 0, 0))
        self.display.blit(t1, (left + 48, top))
        self.display.blit(t2, (left + 48, top + 24))
        self.display.blit(t3, (left + 48, top + 48))

    def drawShop(self):
        left, top = 1048, 144
        textFont = pygame.font.SysFont('Arial', 24, True)
        for option in xrange(6):
            key = option + 1
            text = '(%d) %s $%d' % (key, self.shopTypes[key].__name__,
                                      self.shopCosts[key])
            tSurf = textFont.render(text, 1, (0, 0, 0))
            self.display.blit(tSurf, (left, top + (24 * option)))
        text = '(x) exit'
        tSurf = textFont.render(text, 1, (0, 0, 0))
        self.display.blit(tSurf, (left, top + (24 * 6)))

    def drawGameOver(self):
        left, top = 1000, 144
        text1 = 'Game Over!'
        text2 = '%s wins!!!' % self.winner.color
        text3 = 'Press any key to exit'
        textFont = pygame.font.SysFont('Arial', 24, True)
        t1 = textFont.render(text1, 1, (0, 0, 0))
        t2 = textFont.render(text2, 1, (0, 0, 0))
        t3 = textFont.render(text3, 1, (0, 0, 0))
        self.display.blit(t1, (left + 48, top))
        self.display.blit(t2, (left + 48, top + 24))
        self.display.blit(t3, (left + 48, top + 48))

    def drawHUD(self):
        self.drawBackground()
        self.drawTerrainInfo()
        self.drawUnitInfo()
        self.drawPlayerInfo()
        if self.gameIsOver:
            self.drawGameOver()
        elif self.shopIsOpen:
            self.drawShop()
        elif self.inAttackMode:
            self.drawAttackInstructions()
        elif self.contextMenuIsOpen:
            self.drawContextMenu()
        elif self.unitIsSelected:
            self.drawMovementInstr()
        else:
            self.drawHUDInstr()
        pygame.display.flip()

# testMapPath = os.path.join('maps', 'gauntlet.tpm')
# a = Battle.fromFile(testMapPath)
# a.run()
