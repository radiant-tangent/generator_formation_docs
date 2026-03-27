"""Image augmentations to simulate scan/fax/copy artifacts."""

import io
import os
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageEnhance

AUGMENTATION_PROFILES: dict[str, dict[str, Any]] = {
    "clean": {},
    "slight_scan": {
        "rotation_deg": (-1.5, 1.5),
        "gaussian_noise_std": 3,
        "blur_kernel": 0,
    },
    "moderate_scan": {
        "rotation_deg": (-3, 3),
        "gaussian_noise_std": 8,
        "blur_kernel": 3,
    },
    "heavy_scan": {
        "rotation_deg": (-4, 4),
        "gaussian_noise_std": 15,
        "blur_kernel": 5,
        "jpeg_quality": 65,
    },
    "fax": {
        "rotation_deg": (-1, 1),
        "gaussian_noise_std": 20,
        "blur_kernel": 1,
        "jpeg_quality": 55,
        "contrast_factor": 1.3,
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

    # Apply rotation
    rotation_range = profile.get("rotation_deg")
    if rotation_range:
        low, high = rotation_range
        angle = float(np_rng.uniform(low, high))
        img = _rotate_image(img, angle)

    # Apply Gaussian noise
    noise_std = profile.get("gaussian_noise_std")
    if noise_std:
        img = _add_gaussian_noise(img, noise_std, np_rng)

    # Apply blur
    blur_kernel = profile.get("blur_kernel", 0)
    if blur_kernel > 0:
        img = _apply_blur(img, blur_kernel)

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
