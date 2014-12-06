# mainMenu.py
# by David Simon (dasimon@andrew.cmu.edu)
# Dec 2014

# Based on Advance Wars (Intelligent Systems, Nintendo)

import pygame
from pygame.locals import *
from pygameBaseClass import PygameBaseClass
from map import *
from units import *
from battle import *
from mapEditor import *

class mainMenu(PygameBaseClass):
    def initGraphics(self):
        self.background = self.loadBackground()
        self.title = self.loadTitleSurface()
        self.button = self.loadButton()
        self.highlightedButton = self.loadHighlightedButton()
        self.window = self.loadWindow()

    def beginMusic(self):
        pygame.mixer.music.fadeout(1000)
        musicpath = os.path.join('audio', 'mainMenu.ogg')
        pygame.mixer.music.load(musicpath)
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(1)

    def initGame(self):
        self.modes = ['Battle', 'Edit', 'Quit']
        self.selectionIndex = 0
        self.setupBattle = False
        self.setupEditor = False
        self.editorOpenFiles = False
        self.files = self.getFiles()
        self.beginMusic()
        self.redrawAll()
        self.minRows = self.rows = 10
        self.minCols = self.cols = 16

    def loadBackground(self):
        path = 'menuArt.png'
        image = pygame.image.load(path)
        return image

    def loadTitleSurface(self):
        width = 640
        height = 196
        titleSurface = pygame.Surface((width, height))
        color = pygame.Color('Gray')
        rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(titleSurface, color, rect)
        titleSurface.set_alpha(192)
        font = pygame.font.SysFont('Tahoma', 128, True, True)
        text = "PyWars"
        textSurface = font.render(text, 1, (0, 0, 0))
        vertPadding = 4
        horizPadding = 64
        titleSurface.blit(textSurface, (horizPadding, vertPadding))
        return titleSurface

    def loadButton(self):
        width = 480
        height = 128
        button = pygame.Surface((width, height))
        color = pygame.Color('Gray')
        rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(button, color, rect)
        button.set_alpha(192)
        return button

    def loadHighlightedButton(self):
        width = 480
        height = 128
        button = pygame.Surface((width, height))
        color = pygame.Color('White')
        rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(button, color, rect)
        button.set_alpha(192)
        return button

    def loadWindow(self):
        width = 960
        height = 576
        window = pygame.Surface((width, height))
        color = pygame.Color('Gray')
        rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(window, color, rect)
        return window

    def runBattle(self):
        fileName = self.files[self.selectionIndex] + '.tpm'
        path = os.path.join('maps', fileName)
        battleMode = Battle.fromFile(path)
        if battleMode.runAsChild() == 1: self.quit()
        else: self.initGame()

    def runEditFile(self):
        fileName = self.files[self.selectionIndex] + '.tpm'
        path = os.path.join('maps', fileName)
        editMode = Editor(path)
        if editMode.runAsChild() == 1: self.quit()
        else: self.initGame()

    def runMapEditor(self):
        editMode = Editor((self.rows, self.cols))
        if editMode.runAsChild() == 1: self.quit()
        else: self.initGame()

    def getFiles(self):
        files = []
        for filename in os.listdir('maps'):
            files.append(filename[:len(filename)-4])
        return files

    def select(self):
        mode = self.modes[self.selectionIndex]
        if mode == 'Battle':
            self.setupBattle = True
            self.getFiles()
            self.redrawAll()
        elif mode == 'Edit':
            self.selectionIndex = 0
            self.setupEditor = True
            self.redrawAll()
        elif mode == 'Quit':
            self.quit()

    def menu(self, keyName):
        if keyName == 'return':
            self.select()
        elif keyName == 'escape':
            self.quit()
        elif keyName == 'down':
            self.selectionIndex += 1
            self.selectionIndex %= len(self.modes)
            self.redrawAll()
        elif keyName == 'up':
            self.selectionIndex -= 1
            self.selectionIndex %= len(self.modes)
            self.redrawAll()

    def battleSetup(self, keyName):
        if keyName == 'down':
            self.selectionIndex += 1
            self.selectionIndex %= len(self.files)
            self.redrawAll()
        elif keyName == 'up':
            self.selectionIndex -= 1
            self.selectionIndex %= len(self.files)
            self.redrawAll()
        elif keyName == 'escape':
            self.initGame()
        elif keyName == 'return':
            self.runBattle()
            
    def editSetup(self, keyName):
        if self.editorOpenFiles:
            self.editorOpenFile(keyName)
        elif keyName == 'up':
            self.rows += 1
            self.redrawAll()
        elif keyName == 'down':
            if self.rows > self.minRows:
                self.rows -= 1
                self.redrawAll()
        elif keyName == 'right':
            self.cols += 1
            self.redrawAll()
        elif keyName == 'left':
            if self.cols > self.minCols:
                self.cols -= 1
                self.redrawAll()
        elif keyName == 'o':
            self.editorOpenFiles = True
            self.getFiles()
            self.redrawAll()
        elif keyName == 'return':
            self.runMapEditor()
        elif keyName == 'escape':
            self.initGame()

    def editorOpenFile(self, keyName):
        if keyName == 'return':
            self.runEditFile()
        if keyName == 'up':
            self.selectionIndex -= 1
            self.selectionIndex %= len(self.files)
            self.redrawAll()
        elif keyName == 'down':
            self.selectionIndex += 1
            self.selectionIndex %= len(self.files)
            self.redrawAll()
        elif keyName == 'escape':
            self.editorOpenFiles = False
            self.redrawAll()

    def onKeyDown(self, event):
        keyName = pygame.key.name(event.key)
        if not (self.setupBattle or self.setupEditor):
            self.menu(keyName)
        elif self.setupBattle:
            self.battleSetup(keyName)
        elif self.setupEditor:
            self.editSetup(keyName)

    def drawButton(self, text, isHighlighted, top):
        horizPadding = 96
        vertPadding = 24
        if isHighlighted:
            button = self.highlightedButton.copy()
        else:
            button = self.button.copy()
        font = pygame.font.SysFont('Arial', 64, True)
        buttonText = font.render(text, 1, (0, 0, 0))
        button.blit(buttonText, (horizPadding, vertPadding))
        self.display.blit(button, (0, top))

    def drawMenu(self):
        self.display.blit(self.background, (0, 0))
        self.display.blit(self.title, (0, 0))
        buttonsTop = 256
        buttonHeight = 128
        padding = 16
        for i in xrange(len(self.modes)):
            text = self.modes[i]
            isHighlighted = (i == self.selectionIndex)
            top = buttonsTop + (buttonHeight + padding) * i
            self.drawButton(text, isHighlighted, top)

    def drawBattleSetup(self):
        left, top = 160, 96
        self.display.blit(self.background, (0, 0))
        self.display.blit(self.window, (left, top))
        padding = 8
        fontSize = 32
        font = pygame.font.SysFont('Arial', fontSize, True)
        text = font.render('Maps:', 1, (0, 0, 0))
        self.display.blit(text, (left + 32, top + 24))
        for i in xrange(len(self.files)):
            fileLeft = left + 32
            fileTop = top + 64 + (fontSize + padding) * i
            fileName = self.files[i]
            if i == self.selectionIndex:
                color = (96, 96, 96)
            else:
                color = (0, 0, 0)
            text = font.render(fileName, 1, color)
            self.display.blit(text, (fileLeft, fileTop))

    def drawEditSetup(self):
        left, top = 160, 96
        self.display.blit(self.background, (0, 0))
        self.display.blit(self.window, (left, top))
        fontSize = 32
        font = pygame.font.SysFont('Arial', fontSize, True)
        instructions = ('Use arrow keys to adjust dimensions, or press (o)' +
                        ' to open a file')
        text = font.render(instructions, 1, (0, 0, 0))
        self.display.blit(text, (left + 32, top + 24))
        dimText = '%d rows x %d columns' % (self.rows, self.cols)
        dimensions = font.render(dimText, 1, (0, 0, 0))
        self.display.blit(dimensions, (left + 32, top + 64))

    def redrawAll(self):
        if not (self.setupBattle or self.setupEditor):
            self.drawMenu()
        elif self.setupBattle or self.editorOpenFiles:
            self.drawBattleSetup()
        elif self.setupEditor:
            self.drawEditSetup()
        pygame.display.flip()

PyWars = mainMenu('PyWars')
PyWars.run()
