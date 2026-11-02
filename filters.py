"""Independently implemented spatial filters for this course experiment.

All windows read the ORIGINAL input, never a partially updated output.
Symmetric padding repeats the edge pixel (half-sample symmetry).
No library median/adaptive-median filtering implementation is called.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def _check(image, size):
    a = np.asarray(image)
    if a.ndim != 2 or a.dtype != np.uint8:
        raise ValueError('Input must be a 2-D uint8 grayscale image.')
    if not isinstance(size, int) or size < 3 or size % 2 == 0:
        raise ValueError('Window size must be an odd integer >= 3.')
    return a


def windows(image, size):
    a = _check(image, size)
    return sliding_window_view(np.pad(a, size // 2, mode='symmetric'), (size, size))


def mean_filter(image, size=3):
    """Floating-point arithmetic mean; no rounding before evaluation."""
    return windows(image, size).mean(axis=(-2, -1), dtype=np.float64)


def median_filter(image, size=3):
    w = windows(image, size).reshape(*image.shape, size * size)
    rank = size * size // 2
    return np.partition(w, rank, axis=-1)[..., rank]


def adaptive_median(image, max_size=7, return_maps=False):
    """Two-stage min/median/max AMF with window growth 3, 5, ..., max_size.

    Stage A: min < median < max. Otherwise grow, or return the last
    median at the size limit. Stage B: preserve the original center if
    min < center < max; otherwise use that window's median.
    Only unresolved pixels are gathered at larger windows. This changes
    computation, not the algorithm's output. No noise-generation mask is used.
    """
    a = _check(image, max_size)
    result = a.copy()
    unresolved = np.ones(a.shape, dtype=bool)
    sizes = np.zeros(a.shape, dtype=np.uint8)
    fallback = np.zeros(a.shape, dtype=bool)
    for size in range(3, max_size + 1, 2):
        yy, xx = np.nonzero(unresolved)
        if not len(yy):
            break
        patches = windows(a, size)[yy, xx].reshape(-1, size * size)
        low, high = patches.min(axis=1), patches.max(axis=1)
        rank = size * size // 2
        med = np.partition(patches, rank, axis=1)[:, rank]
        valid = (low < med) & (med < high)
        center = a[yy, xx]
        keep_center = (low < center) & (center < high)
        resolved_value = np.where(keep_center, center, med)
        done = valid if size < max_size else np.ones(len(yy), dtype=bool)
        result[yy[done], xx[done]] = np.where(valid, resolved_value, med)[done]
        sizes[yy[done], xx[done]] = size
        fallback[yy[done], xx[done]] = (~valid)[done]
        unresolved[yy[done], xx[done]] = False
    if return_maps:
        return result, {'window_size': sizes, 'fallback': fallback,
                        'changed': result != a}
    return result


def adaptive_median_reference(image, max_size=7):
    """Slow per-pixel version, used only to verify the vectorized version."""
    a = _check(image, max_size)
    radius = max_size // 2
    padded = np.pad(a, radius, mode='symmetric')
    result = np.empty_like(a)
    for y in range(a.shape[0]):
        for x in range(a.shape[1]):
            for size in range(3, max_size + 1, 2):
                r = size // 2
                p = padded[y+radius-r:y+radius+r+1,
                           x+radius-r:x+radius+r+1]
                lo, mid, hi = p.min(), np.median(p), p.max()
                if lo < mid < hi:
                    result[y, x] = a[y, x] if lo < a[y, x] < hi else mid
                    break
                if size == max_size:
                    result[y, x] = mid
    return result
