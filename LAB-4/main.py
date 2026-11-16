import pygame

from game.game_engine import GameEngine


def main():
    _ = pygame.init()

    # Screen dimensions
    width, height = 600, 500
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Marble Tilt Maze - Pygame Version")

    # Clock
    clock = pygame.time.Clock()
    fps = 60

    # Game loop
    engine: GameEngine = GameEngine(width, height, "medium")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            getattr(engine, "handle_event")(event)

        if engine.quit_requested:
            running = False

        if not engine.game_over:
            getattr(engine, "handle_input")()
        getattr(engine, "update")()
        getattr(engine, "render")(screen)

        pygame.display.flip()
        _ = clock.tick(fps)

    pygame.quit()


if __name__ == "__main__":
    main()
