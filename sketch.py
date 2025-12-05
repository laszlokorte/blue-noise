shape = (size, size)
ranks = np.zeros(shape)

initial_white_noise = np.random.rand(size, size)
placed_pixels = initial_white_noise >= (1-initial_ratio)
count_placed = np.sum(placed_pixels)
count_remaining = placed_pixels.size - count_placed

prev_swap = None

# Phase 1: Place intial
while True:
    blurred = gaussian(placed_pixels)
    densest = (blurred * placed_pixels).argmax()
    voidest = (blurred + placed_pixels).argmin()

    if prev_swap == (voidest, densest):
        break
    if densest == voidest:
        break

    densest_coord = np.unravel_index(densest, shape)
    voidest_coord = np.unravel_index(voidest, shape)

    placed_pixels[densest_coord] = False
    placed_pixels[voidest_coord] = True

    prev_swap = (densest, voidest)

# Phase 2: Rank pixels by density
placed_but_not_ranked = placed_pixels.copy()

for rank in range(count_placed, 0, -1):
    blurred = gaussian(placed_but_not_ranked)
    densest = (blurred * placed_but_not_ranked).argmax()
    densest_coord = np.unravel_index(densest, shape)

    placed_but_not_ranked[densest_coord] = False
    ranks[densest_coord] = rank

# Phase 3: Fill up remaining pixels from the sparsest areas
for rank in range(count_remaining):
    blurred = gaussian(placed_pixels)
    voidest = (blurred + placed_pixels).argmin()
    voidest_coord = np.unravel_index(voidest, shape)

    placed_pixels[voidest_coord] = True
    ranks[voidest_coord] = count_placed + rank

result = ranks