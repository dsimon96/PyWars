# pygameBaseClass.py
# by David Simon (dasimon@andrew.cmu.edu)
# Nov 2014
#
# Changes:
# - Added EXIT condition to allow game to exit
# - Created runAsChild method to allow for nested game objects (menu, game)

import pygame
from pygame.locals import *

class PygameBaseClass(object):
    """Provides a framework for games based on Pygame"""
    def __init__(self, name='PygameBase', width=1280, height=768):
        self.name = name
        self.width = width
        self.height = height

    def createDisplay(self):
        """Creates the display surface"""
        dimensions = (self.width, self.height)
        self.display = pygame.display.set_mode(dimensions)
        pygame.display.set_caption(self.name)

    def onKeyDown(self, event): pass
    def onKeyUp(self, event): pass
    def onMouseMotion(self, event): pass
    def onMouseButtonDown(self, event): pass
    def onMouseButtonUp(self, event): pass
    def redrawAll(self): pass

    def initGraphics(self): pass
    def initGame(self): pass

    def quit(self):
        self.EXIT = True

    def mainloop(self):
        """Handles events"""
        self.EXIT = False
        while self.EXIT == False:
            self.clock.tick(60) # limits the game to 60 frames per second
            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                elif event.type == KEYDOWN:
                    self.onKeyDown(event)
                elif event.type == KEYUP:
                    self.onKeyUp(event)
                elif event.type == MOUSEMOTION:
                    self.onMouseMotion(event)
                elif event.type == MOUSEBUTTONDOWN:
                    self.onMouseButtonDown(event)
                elif event.type == MOUSEBUTTONUP:
                    self.onMouseButtonUp(event)

    def run(self):
        """Run the game"""
        # Set up pygame and the game window
        pygame.init()
        self.createDisplay()

        # Initialize stuff
        self.initGraphics()
        self.initGame()
        self.clock = pygame.time.Clock()
        pygame.display.flip()

        # Call the main loop
        self.mainloop()

        # Clean up
        pygame.quit()

    def runAsChild(self):
        """Allow this class to be run within an already-established object.
        This allows for a parent object (game menu) and child object
        (gamemode)"""
        # Get the display
        self.display = pygame.display.get_surface()

        # Initialize stuff
        self.initGraphics()
        self.initGame()
        self.clock = pygame.time.Clock()
        pygame.display.flip()

        # Call the main loop
        self.mainloop()
        if self.EXIT == False:
            # if this instance is forced to quit, exit out of the parent
            # instance as well
            return 1
