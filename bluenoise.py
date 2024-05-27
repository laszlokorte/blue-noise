from os import path, getcwd
from pathlib import Path
import json

import numpy as np
import skimage.filters as skfilter
from skimage.color import hsv2rgb
from PIL import Image
import matplotlib.pyplot as plt
from scipy.fft import fft2, fftshift

# void and cluster method according to:
# R. A. Ulichney (1988). Dithering with blue noise. Proc. IEEE, 76(1):56-79.
# https://dx.doi.org/10.1117/12.152707

# Related Blog Posts
# http://momentsingraphics.de/BlueNoise.html#_Ulichney93
# https://blog.demofox.org/2019/06/25/generating-blue-noise-textures-with-void-and-cluster/
# https://blog.demofox.org/2018/08/12/not-all-blue-noise-is-created-equal/


class NoopLogger:
    """NoopLogger"""

    def set_phase(self, phase):
        """Do Nothing"""

    def set_step(self, step):
        """Do Nothing"""

    def start_iteration(self):
        """Do Nothing"""

    def step_iteration(self):
        """Do Nothing"""

    def stop_iteration(self):
        """Do Nothing"""

    def log_image(self, name, image):
        """Do Nothing"""

    def log_value(self, name, value):
        """Do Nothing"""

    def write_record(self, filename):
        """Do Nothing"""

    def write_frames(self, filename):
        """Do Nothing"""

def color_scale(gray):
    return hsv2rgb(np.dstack([gray, np.ones_like(gray)*1,gray>0]))


class FileLogger:
    """Logger"""
    # pylint: disable=C0116
    target = None
    current_phase = None
    current_step = 'global'
    current_iteration = None

    buffered_images = []
    buffered_image_sequences = {}
    record = {
        "globals": {},
        "phases": {}
    }
    subdirs = []


    def __init__(self, target_dir):
        self.target = target_dir

    def set_phase(self, phase):
        self.current_step = 0
        self.current_phase = phase

    def set_step(self, step):
        self.current_step = step

    def start_iteration(self):
        self.current_iteration = 0

    def step_iteration(self):
        self.current_iteration += 1

    def stop_iteration(self):
        self.current_iteration = None

    def log_image(self, name, array):
        filename = f"p{self.current_phase:02d}-s{self.current_step:02d}-{name}.png"

        if self.current_iteration is None:
            self.buffered_images.append((filename, np.pad(array, 2) if array.ndim==2 else np.pad(array, [(2,2),(2,2),(0,0)])))
        else:
            if filename not in self.buffered_image_sequences:
                self.buffered_image_sequences[filename] = []
            self.buffered_image_sequences[filename].append(np.pad(array, 2) if array.ndim==2 else np.pad(array, [(2,2),(2,2),(0,0)]))


    def log_value(self, name, value):
        if self.current_phase is None:
            self.record['globals'][name] = value
            return

        if self.current_phase not in self.record['phases']:
            self.record['phases'][self.current_phase] = {
                "static": {},
                "iterations": {},
                "iteration_count": None,
            }

        if self.current_iteration is None:
            self.record['phases'][self.current_phase]['static'][name] = value
        else:
            if name not in self.record['phases'][self.current_phase]['iterations']:
                self.record['phases'][self.current_phase]['iterations'][name] = []
            self.record['phases'][self.current_phase]['iterations'][name].append(value)
            self.record['phases'][self.current_phase]['iteration_count'] = self.current_iteration

    def write_record(self, file_name):
        Path(self.target).mkdir(parents=True, exist_ok=True)
        target = path.join(self.target, file_name)
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(self.record, f, ensure_ascii=False, indent=4)

    def write_frames(self, dir_name):
        Path(path.join(self.target, dir_name)).mkdir(parents=True, exist_ok=True)

        for (filename, array) in self.buffered_images:
            if array.dtype == np.float32 or array.dtype == np.float64:
                array = np.rint(array*255).astype(np.uint8)

            image = Image.fromarray(array)

            image.save(path.join(self.target, dir_name, filename))

        for filename, images in self.buffered_image_sequences.items():
            stack = np.vstack(images)

            if stack.dtype == np.float32 or stack.dtype == np.float64:
                stack = np.rint(stack*255).astype(np.uint8)

            image = Image.fromarray(stack)

            image.save(path.join(self.target, dir_name, filename))

def rescale(arr):
    """Rescale range of array to 0-1"""
    return (arr - np.min(arr)) / np.ptp(arr)

def rescale_max(arr):
    """Rescale range of array to 0-1"""
    return arr / np.max(arr)

def find_densest(mask, sigma, mode="wrap", truncate=4.0, logger = None):
    """Find the maximum in the blurred binary mask to select pixel in densest area"""
    blurred = skfilter.gaussian(mask, sigma=sigma, mode=mode, truncate=truncate)

    if logger is not None:
        blurred_normalized = rescale_max(blurred)
        logger.log_image("blurred", blurred_normalized)
        logger.log_image("blurred_dense_masked", blurred_normalized * mask)

    # if (blurred * mask).argmax() != blurred.argmax():
    #     plt.figure(1)
    #     plt.subplot(211)
    #     plt.imshow(blurred, vmin=0,cmap="grey")
    #     plt.subplot(212)
    #     plt.imshow(blurred * mask, vmin=0,cmap="grey")
    #     plt.show()

    return (blurred * mask).argmax()

def find_voidest(mask, sigma, mode="wrap", truncate=4.0, logger = None):
    """Find the minimum in the blurred binary mask to select pixel in sparsest area"""
    blurred = skfilter.gaussian(mask, sigma=sigma, mode=mode, truncate=truncate)

    if logger is not None:
        blurred_normalized = rescale_max(blurred)
        blurred_plus_mask_normalized = rescale_max(blurred + mask)
        logger.log_image("blurred", blurred_normalized)
        logger.log_image("blurred_voidest_offset", blurred_plus_mask_normalized)

    return ((blurred + mask)).argmin()

def smallest_type(max_number):
    """Returns the smallest numpy type the supports the given maximum number"""
    choices = [np.uint8, np.uint16, np.uint32, np.uint64]
    return next(t for t in choices if max_number <= np.iinfo(t).max)

def bluenoise(size, sigma=2, seed = 23, initial_ratio = 0.1,
              padding_mode="wrap", truncate=4.0, logger = NoopLogger()):
    # pylint: disable=R0913
    """Generates a square blue noise texture"""
    # pylint: disable=R0914
    np.random.seed(seed)
    shape = (size, size)
    ranks = np.zeros(shape, dtype=smallest_type(size*size))
    logger.log_value("width", int(size))
    logger.log_value("height", int(size))
    logger.log_value("seed", float(seed))
    logger.log_value("initial_ratio", float(initial_ratio))
    logger.log_value("sigma", float(sigma))
    logger.log_value("truncate", float(truncate))
    logger.log_value("padding_mode", str(padding_mode))

    # Phase 1: Initialize Black Image with some percent
    # of white pixels (Binary white noise)
    initial_white_noise = np.random.rand(size, size)
    logger.set_phase(1)
    logger.set_step(1)
    logger.log_image("initial_white_noise", initial_white_noise)
    initial_ratio_white = initial_white_noise >= (1-initial_ratio)
    logger.log_value("initial_ratio_white", [(int(x),int(y)) for (x,y) in zip(*np.nonzero(initial_ratio_white))])

    count_white = np.sum(initial_ratio_white)
    to_add = initial_ratio_white.size - count_white

    logger.set_step(2)
    logger.log_image("initial_ratio_white", initial_ratio_white)
    phase1 = initial_ratio_white #.copy()


    logger.set_step(3)
    logger.start_iteration()
    prev = None
    while True:
        logger.step_iteration()
        logger.log_image("before-swap", phase1)

        # Swap pixels between densest and sparsest area
        densest = find_densest(phase1,
                              sigma=sigma,
                              mode=padding_mode,
                              truncate=truncate,
                              logger=logger)
        voidest = find_voidest(phase1,
                               sigma=sigma,
                               mode=padding_mode,
                               truncate=truncate,
                               logger=logger)

        logger.log_value("densest", int(densest))
        logger.log_value("voidest", int(voidest))

        if prev == (voidest, densest):
            break
        if densest == voidest:
            break

        densest_coord = np.unravel_index(densest, shape)
        voidest_coord = np.unravel_index(voidest, shape)

        phase1[densest_coord] = False
        phase1[voidest_coord] = True

        prev = (densest, voidest)
        logger.log_image("after-swap", phase1)
    logger.stop_iteration()

    # Phase 2: remove pixels in descending order from densest
    # to sparsest area in order to number them
    phase2 = phase1.copy()
    logger.set_phase(2)
    logger.log_image("initial", phase2)
    logger.log_value("count_white", int(count_white))

    logger.set_step(1)
    logger.start_iteration()
    for rank in range(count_white, 0, -1):
        logger.step_iteration()
        logger.log_image("before-remove", phase2)

        densest = find_densest(phase2, sigma=sigma,
                              mode=padding_mode, truncate=truncate,
                              logger=logger)
        densest_coord = np.unravel_index(densest, shape)

        phase2[densest_coord] = False
        ranks[densest_coord] = rank
        logger.log_image("after-remove", phase2)
        logger.log_image("after-ranks", ranks/ranks.size)
        logger.log_image("after-ranks-hsv", color_scale(ranks/ranks.size))
        logger.log_value("densest", int(densest))
    logger.stop_iteration()

    # Phase 3: Add more white pixels in sparsest spots until
    # half of all pixels are white
    phase3 = phase1 #.copy() not needed

    logger.set_phase(3)

    logger.log_image("initial", phase3)

    

    logger.set_step(1)
    logger.start_iteration()
    for rank in range(to_add):
        logger.step_iteration()
        logger.log_image("before-new", phase3)

        voidest = find_voidest(phase3,
                               sigma=sigma, mode=padding_mode,
                               truncate=truncate, logger=logger)
        voidest_coord = np.unravel_index(voidest, shape)

        phase3[voidest_coord] = True
        ranks[voidest_coord] = count_white + rank
        logger.log_image("after-new", phase3)
        logger.log_image("after-ranks", ranks/ranks.size)
        logger.log_image("after-ranks-hsv", color_scale(ranks/ranks.size))
        logger.log_value("voidest", int(voidest))

    logger.stop_iteration()
    # count_white += to_add

    # Phase 4: Not needed?
    # phase4 = phase3 # .copy() not needed

    # to_add = phase3.size - count_white

    # for rank in range(to_add):
    #     voidest = find_voidest(phase4, sigma)
    #     voidest_coord = np.unravel_index(voidest, phase4.shape)

    #     phase4[voidest_coord] = True
    #     ranks[voidest_coord] = count_white + rank

    return ranks


def example_plot(size, logger):
    """Creates an example noise texture using the function 
    above and plots it together with its spectrogram.
    The spectrogram is expected to have a dark spot in the low frequencies in order
    to actually being blue noise"""

    # pylint: disable=C0415
    eps = np.finfo(np.float32).eps

    space_quantized = bluenoise(size, sigma=1, initial_ratio=0.1, truncate=4,logger=logger)

    logger.set_phase(5)
    space = space_quantized/space_quantized.size


    logger.log_image('result', space)
    logger.log_image('result-hsv', color_scale(space))
    spec = fftshift(fft2(space))
    psd = np.abs(spec*np.conj(spec))
    log_psd = np.log(psd+eps)
    log_psd[size//2,size//2] = 0 # set DC frequency to 0
    psd[size//2,size//2] = 0 # set DC frequency to 0
    logger.log_image('psd', rescale(psd))
    logger.log_image('log-psd', rescale(log_psd))

    # Print Result as SVG Rects
    # rescaled_log_psd = log_psd / np.max(log_psd)
    # for y in range(rescaled_log_psd.shape[0]):
    #     for x in range(rescaled_log_psd.shape[1]):
    #         print(f'<rect x="{x}" y="{y}" width="1" height="1"
    #               fill="hsl(0,0%,{int(100*rescaled_log_psd[y][x])}%)" />')

    plt.figure(1)
    plt.suptitle("Blue Noise", fontsize=16)
    plt.subplot(331)
    plt.title("Texture")
    plt.imshow(space, vmin=0, vmax=1,cmap="grey")
    plt.subplot(332)
    plt.title("PSD")
    plt.imshow(psd, vmin=0, cmap="grey")
    plt.subplot(333)
    plt.title("Log PSD")
    plt.imshow(log_psd, vmin=0,cmap="grey")

    logger.set_step(1)
    thres = space >= 0.9
    thres_spec = fftshift(fft2(thres))
    thres_psd = np.abs(thres_spec*np.conj(thres_spec))
    log_thres_psd = np.log(thres_psd+eps)
    log_thres_psd[size//2,size//2] = 0 # set DC frequency to 0
    thres_psd[size//2,size//2] = 0 # set DC frequency to 0
    logger.log_image('thresholded', thres)
    logger.log_image('thresholded-psd', rescale(thres_psd))
    logger.log_image('thresholded-log-psd', rescale(log_thres_psd))

    plt.subplot(334)
    plt.title("Thresholded")
    plt.imshow(thres, vmin=0, vmax=1,cmap="grey")
    plt.subplot(335)
    plt.title("Thresholded PSD")
    plt.imshow(thres_psd, vmin=0, cmap="grey")
    plt.subplot(336)
    plt.title("Thresholded Log PSD")
    plt.imshow(log_thres_psd, vmin=0,cmap="grey")


    white = np.random.rand(size, size) > 0.1
    white_spec = fftshift(fft2(white))
    white_psd = np.abs(white_spec*np.conj(white_spec))
    log_white_psd = np.log(white_psd+eps)
    log_white_psd[size//2,size//2] = 0 # set DC frequency to 0
    white_psd[size//2,size//2] = 0 # set DC frequency to 0

    plt.subplot(337)
    plt.title("whiteholded")
    plt.imshow(white, vmin=0, vmax=1, cmap="grey")
    plt.subplot(338)
    plt.title("whiteholded PSD")
    plt.imshow(white_psd, vmin=0, cmap="grey")
    plt.subplot(339)
    plt.title("whiteholded Log PSD")
    plt.imshow(log_white_psd, vmin=0, cmap="grey")

    plt.show()

    logger.write_frames('src/steps')
    logger.write_record('recording.json')


if __name__ == "__main__":
    example_plot(32, FileLogger('.'))
