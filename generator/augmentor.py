"""Image augmentations to simulate scan/fax/copy artifacts."""

import io
import os
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

AUGMENTATION_PROFILES: dict[str, dict[str, Any]] = {
    "slight_scan": {
        "rotation_deg": (-1.5, 1.5),
        "gaussian_noise_std": 3,
        "blur_kernel": 0,
        "background_tint": (0.02, 0.06),
        "brightness_shift": (-10, 10),
        "margin_shift_px": (-8, 8),
    },
    "moderate_scan": {
        "rotation_deg": (-3, 3),
        "gaussian_noise_std": 8,
        "blur_kernel": 1,
        "scanner_shadow": (15, 30),
        "perspective_warp": (0.002, 0.006),
        "background_tint": (0.03, 0.08),
        "brightness_shift": (-15, 15),
        "margin_shift_px": (-15, 15),
        "salt_pepper_prob": 0.0005,
    },
    "heavy_scan": {
        "rotation_deg": (-4, 4),
        "gaussian_noise_std": 15,
        "blur_kernel": 5,
        "jpeg_quality": 65,
        "scanner_shadow": (25, 50),
        "perspective_warp": (0.005, 0.012),
        "background_tint": (0.05, 0.12),
        "brightness_shift": (-25, 25),
        "margin_shift_px": (-20, 20),
        "salt_pepper_prob": 0.002,
        "vignette_strength": (0.3, 0.6),
    },
    "fax": {
        "rotation_deg": (-1, 1),
        "gaussian_noise_std": 20,
        "blur_kernel": 1,
        "jpeg_quality": 55,
        "contrast_factor": 1.3,
        "background_tint": (0.06, 0.15),
        "brightness_shift": (-20, 20),
        "salt_pepper_prob": 0.003,
        "scanner_shadow": (10, 25),
        "perspective_warp": (0.002, 0.005),
        "vignette_strength": (0.2, 0.5),
    },
}


def _rotate_image(img: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image by a given angle, filling borders with white."""
    h, w = img.shape[:2]
    center = (w / 2, h / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        img, matrix, (w, h),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )


def _add_gaussian_noise(img: np.ndarray, std: float, np_rng: np.random.Generator) -> np.ndarray:
    """Add Gaussian noise to an image."""
    noise = np_rng.normal(0, std, img.shape).astype(np.float64)
    noisy = img.astype(np.float64) + noise
    return np.clip(noisy, 0, 255).astype(np.uint8)


def _apply_blur(img: np.ndarray, kernel_size: int) -> np.ndarray:
    """Apply Gaussian blur with the given kernel size."""
    if kernel_size <= 0:
        return img
    # Kernel must be odd
    k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
    return cv2.GaussianBlur(img, (k, k), 0)


def _jpeg_compress(img: np.ndarray, quality: int) -> np.ndarray:
    """Simulate JPEG compression artifacts."""
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    pil_img = Image.open(buffer)
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def _adjust_contrast(img: np.ndarray, factor: float) -> np.ndarray:
    """Adjust image contrast using PIL."""
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    enhanced = ImageEnhance.Contrast(pil_img).enhance(factor)
    return cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2BGR)


def _apply_background_tint(img: np.ndarray, strength: float, np_rng: np.random.Generator) -> np.ndarray:
    """Tint the white background to simulate aged or off-white paper."""
    # Generate a warm/cool tint that varies per-channel
    tint = np_rng.uniform(-0.3, 1.0, size=3).astype(np.float64)
    tint = tint / (np.linalg.norm(tint) + 1e-8)  # normalize direction
    # Scale by strength (0-1 range where strength controls how far from white)
    shift = tint * strength * 255.0

    result = img.astype(np.float64)
    # Only tint pixels that are relatively bright (paper, not ink)
    brightness = np.mean(result, axis=2)
    mask = (brightness > 180).astype(np.float64)[:, :, np.newaxis]
    result = result - mask * np.abs(shift)
    return np.clip(result, 0, 255).astype(np.uint8)


def _apply_scanner_shadow(img: np.ndarray, shadow_width: int) -> np.ndarray:
    """Add dark edge shadows simulating a flatbed scanner."""
    h, w = img.shape[:2]
    result = img.astype(np.float64)

    for edge_w in range(shadow_width):
        alpha = 1.0 - (edge_w / shadow_width) * 0.4  # darken up to 40%
        # Top edge
        result[edge_w, :] *= alpha
        # Bottom edge
        result[h - 1 - edge_w, :] *= alpha
        # Left edge
        result[:, edge_w] *= alpha
        # Right edge
        result[:, w - 1 - edge_w] *= alpha

    return np.clip(result, 0, 255).astype(np.uint8)


def _apply_perspective_warp(img: np.ndarray, warp_strength: float, np_rng: np.random.Generator) -> np.ndarray:
    """Apply a subtle perspective transform simulating non-flat page on scanner."""
    h, w = img.shape[:2]
    max_offset = warp_strength * max(h, w)

    # Source corners
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])

    # Randomly perturb each corner
    offsets = np_rng.uniform(-max_offset, max_offset, size=(4, 2)).astype(np.float32)
    dst = src + offsets

    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(
        img, matrix, (w, h),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )


def _apply_brightness_shift(img: np.ndarray, shift: float) -> np.ndarray:
    """Shift overall brightness to simulate variable scanner exposure."""
    result = img.astype(np.float64) + shift
    return np.clip(result, 0, 255).astype(np.uint8)


def _apply_margin_shift(img: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """Translate the image to simulate page placement variation on scanner."""
    h, w = img.shape[:2]
    matrix = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(
        img, matrix, (w, h),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )


def _apply_salt_pepper_noise(img: np.ndarray, prob: float, np_rng: np.random.Generator) -> np.ndarray:
    """Add salt-and-pepper noise (speckling) to simulate dust/dirt."""
    result = img.copy()
    rand = np_rng.random(img.shape[:2])
    # Salt (white)
    result[rand < prob / 2] = 255
    # Pepper (black)
    result[(rand > 1.0 - prob / 2)] = 0
    return result


def _apply_vignette(img: np.ndarray, strength: float) -> np.ndarray:
    """Apply vignette (darkened corners) simulating scanner light falloff."""
    h, w = img.shape[:2]
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    # Distance from center, normalized to 0-1
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    max_dist = np.sqrt(cx ** 2 + cy ** 2)
    dist = dist / max_dist
    # Vignette mask: 1. at center, darkens toward edges
    mask = 1.0 - strength * (dist ** 2)
    mask = mask[:, :, np.newaxis]
    result = img.astype(np.float64) * mask
    return np.clip(result, 0, 255).astype(np.uint8)


def augment_image(
    input_path: str,
    output_path: str,
    profile_name: str,
    np_rng: np.random.Generator,
) -> str:
    """Apply augmentations to a base image and save the result.

    Args:
        input_path: Path to the source PNG image.
        output_path: Path to save the augmented image.
        profile_name: Name of the augmentation profile to apply.
        np_rng: Seeded numpy random generator.

    Returns:
        Path to the saved augmented image.
    """
    profile = AUGMENTATION_PROFILES.get(profile_name, {})

    if not profile:
        # Clean profile: just copy
        if input_path != output_path:
            import shutil
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.copy2(input_path, output_path)
        return output_path

    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {input_path}")

    # Apply margin/offset shift (before rotation so edges stay clean)
    margin_range = profile.get("margin_shift_px")
    if margin_range:
        low, high = margin_range
        dx = int(np_rng.integers(low, high + 1))
        dy = int(np_rng.integers(low, high + 1))
        img = _apply_margin_shift(img, dx, dy)

    # Apply perspective warp
    warp_range = profile.get("perspective_warp")
    if warp_range:
        low, high = warp_range
        strength = float(np_rng.uniform(low, high))
        img = _apply_perspective_warp(img, strength, np_rng)

    # Apply rotation
    rotation_range = profile.get("rotation_deg")
    if rotation_range:
        low, high = rotation_range
        angle = float(np_rng.uniform(low, high))
        img = _rotate_image(img, angle)

    # Apply background tint (paper aging/color)
    tint_range = profile.get("background_tint")
    if tint_range:
        low, high = tint_range
        strength = float(np_rng.uniform(low, high))
        img = _apply_background_tint(img, strength, np_rng)

    # Apply brightness shift
    brightness_range = profile.get("brightness_shift")
    if brightness_range:
        low, high = brightness_range
        shift = float(np_rng.uniform(low, high))
        img = _apply_brightness_shift(img, shift)

    # Apply Gaussian noise
    noise_std = profile.get("gaussian_noise_std")
    if noise_std:
        img = _add_gaussian_noise(img, noise_std, np_rng)

    # Apply salt and pepper noise
    sp_prob = profile.get("salt_pepper_prob")
    if sp_prob:
        img = _apply_salt_pepper_noise(img, sp_prob, np_rng)

    # Apply blur
    blur_kernel = profile.get("blur_kernel", 0)
    if blur_kernel > 0:
        img = _apply_blur(img, blur_kernel)

    # Apply scanner edge shadows
    shadow_range = profile.get("scanner_shadow")
    if shadow_range:
        low, high = shadow_range
        shadow_w = int(np_rng.integers(low, high + 1))
        img = _apply_scanner_shadow(img, shadow_w)

    # Apply vignette
    vignette_range = profile.get("vignette_strength")
    if vignette_range:
        low, high = vignette_range
        strength = float(np_rng.uniform(low, high))
        img = _apply_vignette(img, strength)

    # Apply JPEG compression
    jpeg_quality = profile.get("jpeg_quality")
    if jpeg_quality:
        img = _jpeg_compress(img, jpeg_quality)

    # Apply contrast adjustment
    contrast_factor = profile.get("contrast_factor")
    if contrast_factor:
        img = _adjust_contrast(img, contrast_factor)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, img)
    return output_path
