from solver import solve
# from mooing15 import solve
# from my_solver import solve

#V3.0 

# Check out this video for more information: https://youtu.be/uGbZPrpFsI8?t=2086

# This solver can be used to find a sequence of merges that is optimal in terms of
# the number of generated keys and unlocking tiles for progress (favoring full keys over
# unlocking tiles)

# The solver only works on one color at the time, so do each color in turn.

# The solver is designed to be used before you have started to merge gems. 
# If you have already started a board and want to check, you can change the 
# "Optional" lists, but make sure to set them back to [0,0,0,0] after.

# Update all the values below, then hit the "run" (triangle) button.
# Keep in mind you have to do this for each color on each board

# Number of Locked Gems. "l1" = gem level 1, "l2" = gem level 2, etc. "b" = bottom key piece, "t" = top key piece.
l1b = 1
l1t = 0
l2b = 5
l2t = 1
l3b = 2
l3t = 1
l4b = 0
l4t = 0

# Number of Free Gems. These are the ones that you spawned
l1 = 5
l2 = 2
l3 = 1
l4 = 1

# Optional. Number of free gems with a key piece or full key. Format is [l1,l2,l3,l4].
# This will be all 0 for a new board
free_bottom = [0,0,0,0]
free_top = [0,0,0,0]
free_full = [0,0,0,0]












### Do not change anything below here
locked_bottom = [l1b,l2b,l3b,l4b]
locked_top = [l1t,l2t,l3t,l4t]
free = [l1,l2,l3,l4]

solve(locked_bottom,locked_top,free,free_bottom,free_top,free_full)
