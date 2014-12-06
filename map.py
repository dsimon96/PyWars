# map.py
# by David Simon (dasimon@andrew.cmu.edu)
# Dec 2014

# Sprites from Advance Wars (Intelligent Systems, Nintendo)

import os
import pygame
from pygame.locals import *
from pygameBaseClass import PygameBaseClass

class Tile(pygame.sprite.Sprite):
    """
    Represents a single tile

    Each tile has a terrainType, an integer corresponding to a certain terrain
    """
    size = 64 # size of each tile in pixels
    defaultType = 1 # default type for blank maps
    terrainTypeNames = {
        0: 'Sea',
        1: 'Plain',
        2: 'Road',
        3: 'Forest',
        4: 'Mountain',
        5: 'River',
        6: 'Bridge'
    }
    defenseValues = {
        0: 0,
        1: 1,
        2: 0,
        3: 2,
        4: 3,
        5: 0,
        6: 0
    } # defense factor for each terrain type. Used in damage calculations
    dynamicSpriteTypes = {0, 2, 5, 6} # terrain types w/ dynamic sprites
    staticSpriteFiles = {
        0: "WaterOpen.png",
        1: "Grass.png",
        2: "RoadHoriz.png",
        3: "Forest.png",
        4: "Mountain.png",
        5: "RiverHoriz.png",
        6: "BridgeHoriz.png"
    } # static terrain types and their corresponding terrain types
    roadFiles = {
        '0000': "RoadHoriz.png",
        '0001': "RoadHoriz.png",
        '0010': "RoadVert.png",
        '0011': "RoadCorner2.png",
        '0100': "RoadHoriz.png",
        '0101': "RoadHoriz.png",
        '0110': "RoadCorner1.png",
        '0111': "RoadT1.png",
        '1000': "RoadVert.png",
        '1001': "RoadCorner3.png",
        '1010': "RoadVert.png",
        '1011': "RoadT2.png",
        '1100': "RoadCorner4.png",
        '1101': "RoadT3.png",
        '1110': "RoadT4.png",
        '1111': "RoadInter.png"
    } # Maps cardinal directions surrounding a road to the corr. sprite file
    waterFiles = {
        '0000': "WaterIsolated.png",
        '0001': "WaterU2.png",
        '0010': "WaterU1.png",
        '0011': "WaterCorner2.png",
        '0100': "WaterU4.png",
        '0101': "WaterHoriz.png",
        '0110': "WaterCorner1.png",
        '0111': "WaterBorder1.png",
        '1000': "WaterU3.png",
        '1001': "WaterCorner3.png",
        '1010': "WaterVert.png",
        '1011': "WaterBorder2.png",
        '1100': "WaterCorner4.png",
        '1101': "WaterBorder3.png",
        '1110': "WaterBorder4.png",
        '1111': "WaterOpen.png"
    } # Maps cardinal directions surrounding water to the corr. sprite file
    riverFiles = {
        '0000': "RiverHoriz.png",
        '0001': "RiverHoriz.png",
        '0010': "RiverVert.png",
        '0011': "RiverCorner2.png",
        '0100': "RiverHoriz.png",
        '0101': "RiverHoriz.png",
        '0110': "RiverCorner1.png",
        '0111': "RiverHoriz.png",
        '1000': "RiverVert.png",
        '1001': "RiverCorner3.png",
        '1010': "RiverVert.png",
        '1011': "RiverVert.png",
        '1100': "RiverCorner4.png",
        '1101': "RiverHoriz.png",
        '1110': "RiverVert.png",
        '1111': "RiverInter.png"
    } # Maps cardinal directions surrounding water to the corr. sprite file

    def __init__(self, terrainType, surroundings):
        super(Tile, self).__init__()
        self.terrainType = terrainType
        self.surroundings = surroundings
        self.image = self.getImage()
        self.name = self.terrainTypeNames[terrainType]
        self.staticImage = self.getStaticImage()
        self.height = self.image.get_height()
        self.overflow = self.height - Tile.size
        self.defense = Tile.defenseValues[terrainType]

    def getBridgeImage(self, cardinalsIdentifier):
        cardinalsIdentifier = self.getCardinalsIdentifier(5)
        n = int(cardinalsIdentifier[0])
        e = int(cardinalsIdentifier[1])
        s = int(cardinalsIdentifier[2])
        w = int(cardinalsIdentifier[3])
        if (e == 1 or w == 1) and not (n == 1 or s == 1):
            return 'BridgeVert.png'
        else:
            return 'BridgeHoriz.png'

    def getCardinalsIdentifier(self, terrType):
        neswIndex = [1, 4, 6, 3] # Indices for cardinal directions
        cardinalsIdentifier = ''
        for index in neswIndex:
            tileType = self.surroundings[index]
            if tileType == terrType or tileType == None:
                cardinalsIdentifier += '1'
            else:
                cardinalsIdentifier += '0'
        return cardinalsIdentifier

    def getDynamicImage(self, terrType):
        """Get the appropriate filename for the terrain based on the
        surroundings"""
        cardinalsIdentifier = self.getCardinalsIdentifier(terrType)
        if terrType == 0:
            return self.waterFiles[cardinalsIdentifier]
        elif terrType == 2:
            return self.roadFiles[cardinalsIdentifier]
        elif terrType == 5:
            return self.riverFiles[cardinalsIdentifier]
        elif terrType == 6:
            return self.getBridgeImage(cardinalsIdentifier)

    def getImage(self):
        """Gets the appropriate sprite for this tile"""
        if self.terrainType in Tile.dynamicSpriteTypes:
            filename = self.getDynamicImage(self.terrainType)
        else:
            filename = Tile.staticSpriteFiles[self.terrainType]
        path = os.path.join('tiles', filename)
        image = pygame.image.load(path)
        return image

    def getStaticImage(self):
        filename = Tile.staticSpriteFiles[self.terrainType]
        path = os.path.join('tiles', filename)
        image = pygame.image.load(path)
        return image

class Objective(Tile):
    teams = {
        0: 'Red',
        1: 'Blue',
        2: 'Green',
        3: 'Yellow',
        4: 'Empty'
    }
    types = {
        0: 'HQ',
        1: 'City',
        2: 'Factory'
    }
    defenseValues = {
        0: 5,
        1: 4,
        2: 4
    }
    baseHealth = 20

    def __init__(self, teamAndType):
        self.terrainType = 7
        self.teamNum, self.typeNum = teamAndType
        self.team = Objective.teams[self.teamNum]
        self.type = Objective.types[self.typeNum]
        self.name = self.type
        self.health = Objective.baseHealth
        self.image = self.getImage()
        self.staticImage = self.image
        self.height = self.image.get_height()
        self.overflow = self.height - Tile.size
        self.defense = Objective.defenseValues[self.typeNum]

    def getImage(self):
        filename = self.team + self.type + '.png'
        path = os.path.join('tiles', filename)
        image = pygame.image.load(path)
        return image
        
class Map(pygame.sprite.Sprite):
    """
    Represents an in-game map
    """
    def __init__(self, contents=None):
        super(Map, self).__init__()
        if type(contents) == tuple:
            contents = self.blankMap(contents)
        else:
            contents = self.loadContents(contents)
        self.rows = len(contents)
        self.cols = len(contents[0])
        self.width = self.cols * Tile.size
        self.height = self.rows * Tile.size
        self.contents = contents
        self.map = self.getMap(contents)
        self.defense = self.getDefense()
        self.image = self.getImage()
        self.objectives = self.getObjectives()

    def refreshImage(self):
        self.image = self.getImage()

    def getObjectives(self):
        objectives = []
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                tile = self.map[row][col]
                if isinstance(tile, Objective):
                    objectives.append((row, col, tile))
        return objectives

    @staticmethod
    def blankMap(dimensions):
        """Generates a blank map"""
        rows, cols = dimensions
        contents = []
        for row in xrange(rows):
            contents += [[Tile.defaultType] * cols]
        return contents

    def getMap(self, contents):
        """Translates the list of contents into a map"""
        map = []
        for row in xrange(self.rows):
            thisRow = []
            for col in xrange(self.cols):
                terrainType = contents[row][col]
                if type(terrainType) == int:
                    tile = Tile(terrainType,
                                self.getSurroundingTiles(row, col))
                else:
                    tile = Objective(terrainType)
                thisRow += [tile]
            map.append(thisRow)
        return map

    def deleteHQ(self, team):
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                tile = self.map[row][col]
                if (isinstance(tile, Objective) and tile.typeNum == 0 and
                    tile.teamNum == team):
                    self.changeTile(Tile.defaultType, (row, col))


    def changeTile(self, terrType, coords):
        row, col = coords
        if type(terrType) == int:
            self.contents[row][col] = terrType
            self.map[row][col] = Tile(terrType,
                                      self.getSurroundingTiles(row, col))
            self.updateSurroundings(coords)
        else:
            self.contents[row][col] = terrType
            if terrType[1] == 0:
                self.deleteHQ(terrType[0])
            self.map[row][col] = Objective(terrType)
            self.updateSurroundings(coords)
        self.refreshImage()

    def getSurroundingTiles(self, row, col):
        """Get a list of all of the tiles surrounding (row, col)"""
        range = [-1, 0, 1]
        surroundings = []
        for dRow in range:
            for dCol in range:
                if (dRow, dCol) != (0, 0): # Ignore center tile
                    newRow = row + dRow
                    newCol = col + dCol
                    if (newRow < 0 or newRow >= self.rows or
                        newCol < 0 or newCol >= self.cols):
                        # Ensure that the checked tile is on the map
                        terrainType = None
                    else:
                        terrainType = self.contents[newRow][newCol]
                    surroundings.append(terrainType)
        return surroundings

    def getDefense(self):
        """Creates and populates a 2D list representing defense factor for
        each tile in the map"""
        defenseValues = []
        # create an empty, appropriately sized 2D list
        for row in xrange(self.rows):
            defenseValues += [[None] * self.cols]
        # populate the list with restrictions
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                tile = self.map[row][col]
                defenseValues[row][col] = tile.defense
        return defenseValues

    def updateSurroundings(self, coords):
        dirs = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        cRow, cCol = coords
        for (dRow, dCol) in dirs:
            newRow, newCol = cRow + dRow, cCol + dCol
            if (0 <= newRow < self.rows and 0 <= newCol < self.cols):
                tile = self.map[newRow][newCol]
                if not isinstance(tile, Objective):
                    terrType = tile.terrainType
                    self.map[newRow][newCol] = Tile(terrType,
                        self.getSurroundingTiles(newRow, newCol))

    def getImage(self):
        """Creates a surface with the appearance of the map"""
        image = pygame.Surface((self.width, self.height))
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                tile = self.map[row][col]
                top = row * Tile.size - tile.overflow
                left = col * Tile.size
                width = height = Tile.size
                dest = (left, top, width, height)
                image.blit(tile.image, dest)
        return image

    @staticmethod
    def loadContents(contentString):
        rows = contentString.splitlines()
        map = []
        for row in rows:
            cols = row.split()
            mapRow = []
            for tile in cols:
                if len(tile) == 2:
                    team = int(tile[0])
                    type = int(tile[1])
                    mapRow.append((team, type))
                else:
                    terrType = int(tile)
                    mapRow.append(terrType)
            map.append(mapRow)
        return map

# class MapTest(PygameBaseClass):
#     """A 15x10 map to debug the map and tile classes"""
#     def __init__(self):
#         super(MapTest, self).__init__('Map Test',15*64,10*64)
#
#     def initGame(self):
#         testMap = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
#                    [0,0,(0,2),(0,1),1,1,1,1,0,0,0,0,0,0,0],
#                    [0,(0,0),2,2,3,3,3,1,1,1,1,0,0,0,0],
#                    [0,1,1,2,1,3,3,3,3,1,1,1,1,0,0],
#                    [0,1,1,2,1,1,1,3,3,3,1,1,1,0,0],
#                    [0,0,1,2,2,2,2,2,2,2,2,2,1,0,0],
#                    [0,0,1,1,1,3,3,3,1,2,0,2,1,1,0],
#                    [0,0,1,1,4,4,3,1,1,2,2,2,2,(1,0),0],
#                    [0,0,0,1,1,1,1,1,1,1,1,(1,1),(1,2),0,0],
#                    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
#         a = Map((15,10), testMap)
#         self.screen.blit(a.image, (0,0))
#
# if __name__ == '__main__':
#     MapTest().run()