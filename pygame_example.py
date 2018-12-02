# # # # #
# CONSTANTS

DUMMY = False
RES = (640,480)


# # # # #
# IMPORTS

# external
import pygame

# custom
if not DUMMY:
    from mpydev import BioPac


# # # # #
# STARTUP

# Initialize PyGame.
pygame.init()

# Create a new display.
disp = pygame.display.set_mode(RES, pygame.RESIZABLE)

# Initialise a font to display text.
font = pygame.font.Font(pygame.font.get_default_font(), 24)

# Start communication with a BioPac MP150 device.
if not DUMMY:
    mp = BioPac("MP150", n_channels=3, samplerate=200, logfile="test", overwrite=True)


# # # # #
# RUN

# Run until the user quits.
quited = False
while not quited:

    # Start recording data to file.
    if not DUMMY:
        mp.start_recording()

    # Get the newest sample. Note that you DO NOT have to do this to record
    # data! Data is recorded in the background after calling 'start_recording',
    # the sample method is only here to use samples within the experiment,
    # for example to create a visual effect.
    if not DUMMY:
        sample = mp.sample()
    else:
        sample = 16 * [0.0]

    # Render text.
    textsurf = font.render("sample = %.3f, %.3f, %.3f" % (sample[0], sample[1], sample[2]), False, (255,255,255))
    blitpos = (int(RES[0]/2 - textsurf.get_width()/2), int(RES[1]/2 - textsurf.get_height()/2))
    
    # Blit text to the display Surface.
    disp.fill((0,0,0))
    disp.blit(textsurf, blitpos)
    
    # Update the display.
    pygame.display.flip()
    
    # Check if there was any keyboard input.
    for event in pygame.event.get(pygame.KEYDOWN):
        if pygame.key.name(event.key) == 'escape':
            quited = True

# Stop recording data.
if not DUMMY:
    mp.stop_recording()


# # # # #
# CLOSE

# Close the connection to the BIOPAC device.
if not DUMMY:
    mp.close()

# Close the display.
pygame.display.quit()
