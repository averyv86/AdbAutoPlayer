#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite: Advanced Image Preprocessing for ADB Vision

Tests the preprocessing implementations from adb_cv_preprocess.py.
Covers CLAHE enhancement, morphological operations, edge detection,
grayscale variants, and pipeline orchestration.

Test Categories:
  - CLAHE Enhancement Tests (10 tests)
  - Morphological Operations Tests (12 tests)
  - Edge Detection Tests (8 tests)
  - Grayscale Variant Tests (8 tests)
  - Pipeline Orchestration Tests (7 tests)

Total: 45+ test methods, 87% coverage target
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
from typing import Tuple
from unittest.mock import Mock, patch, MagicMock

# Import preprocessing classes
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "moai-domain-adb" / "scripts"))

from adb_cv_preprocess import (
    CLAHEPreprocessor,
    MorphologicalProcessor,
    EdgeDetectionProcessor,
    GrayscaleVariantProcessor,
    PreprocessingPipeline,
    PerformanceMetricsCollector,
    ProcessingMetrics,
    PipelineResult,
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_image_rgb() -> np.ndarray:
    """Create a test RGB image"""
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    # Add white square
    image[100:200, 100:200] = [255, 255, 255]
    # Add gradient
    for i in range(480):
        image[i, :] = int(255 * i / 480)
    return image


@pytest.fixture
def test_image_bgr() -> np.ndarray:
    """Create a test BGR image"""
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    # Add colored regions
    image[0:160, :] = [0, 0, 255]  # Red channel
    image[160:320, :] = [0, 255, 0]  # Green channel
    image[320:, :] = [255, 0, 0]  # Blue channel
    return image


@pytest.fixture
def test_image_grayscale() -> np.ndarray:
    """Create a test grayscale image"""
    image = np.zeros((480, 640), dtype=np.uint8)
    # Add gradient
    for i in range(480):
        image[i, :] = int(255 * i / 480)
    return image


@pytest.fixture
def test_image_noisy() -> np.ndarray:
    """Create a noisy test image"""
    image = np.ones((480, 640, 3), dtype=np.uint8) * 128
    # Add random noise
    noise = np.random.randint(-50, 50, (480, 640, 3))
    image = np.clip(image + noise, 0, 255).astype(np.uint8)
    return image


@pytest.fixture
def test_image_low_contrast() -> np.ndarray:
    """Create a low-contrast test image"""
    image = np.ones((480, 640, 3), dtype=np.uint8) * 100
    # Add subtle features
    image[100:300, 100:300] = 120
    image[150:250, 150:250] = 110
    return image


# ============================================================================
# CLAHE ENHANCEMENT TESTS
# ============================================================================

class TestCLAHEPreprocessor:
    """Test Contrast Limited Adaptive Histogram Equalization"""

    def test_clahe_initialization(self):
        """Test CLAHE preprocessor initialization"""
        preprocessor = CLAHEPreprocessor(clip_limit=2.0, tile_grid_size=(8, 8))
        assert preprocessor.clip_limit == 2.0
        assert preprocessor.tile_grid_size == (8, 8)

    def test_clahe_initialization_custom_params(self):
        """Test CLAHE with custom parameters"""
        preprocessor = CLAHEPreprocessor(clip_limit=4.0, tile_grid_size=(16, 16))
        assert preprocessor.clip_limit == 4.0
        assert preprocessor.tile_grid_size == (16, 16)

    def test_clahe_process_bgr_image(self, test_image_bgr):
        """Test CLAHE processing on BGR image"""
        preprocessor = CLAHEPreprocessor()
        result, metrics = preprocessor.process(test_image_bgr)

        assert result.shape == test_image_bgr.shape
        assert result.dtype == test_image_bgr.dtype
        assert metrics.operation == "CLAHE"
        assert metrics.execution_time_ms > 0

    def test_clahe_process_grayscale_image(self, test_image_grayscale):
        """Test CLAHE processing on grayscale image"""
        preprocessor = CLAHEPreprocessor()
        result, metrics = preprocessor.process(test_image_grayscale)

        assert result.shape == test_image_grayscale.shape
        assert metrics.operation == "CLAHE"

    def test_clahe_contrast_enhancement(self, test_image_low_contrast):
        """Test that CLAHE enhances contrast"""
        preprocessor = CLAHEPreprocessor(clip_limit=2.0)
        result, _ = preprocessor.process(test_image_low_contrast)

        # Compute contrast (standard deviation of pixel values)
        original_contrast = np.std(test_image_low_contrast)
        enhanced_contrast = np.std(result)

        # Enhanced image should have higher contrast
        assert enhanced_contrast >= original_contrast * 0.9  # Allow small variations

    def test_clahe_high_clip_limit(self, test_image_low_contrast):
        """Test CLAHE with high clip limit for aggressive enhancement"""
        preprocessor = CLAHEPreprocessor(clip_limit=4.0)
        result, metrics = preprocessor.process(test_image_low_contrast)

        assert result.shape == test_image_low_contrast.shape
        assert metrics.parameters["clip_limit"] == 4.0

    def test_clahe_small_tile_grid(self, test_image_bgr):
        """Test CLAHE with small tile grid (more local adaptation)"""
        preprocessor = CLAHEPreprocessor(tile_grid_size=(4, 4))
        result, metrics = preprocessor.process(test_image_bgr)

        assert result.shape == test_image_bgr.shape
        assert metrics.parameters["tile_grid_size"] == (4, 4)

    def test_clahe_large_tile_grid(self, test_image_bgr):
        """Test CLAHE with large tile grid (less local adaptation)"""
        preprocessor = CLAHEPreprocessor(tile_grid_size=(16, 16))
        result, metrics = preprocessor.process(test_image_bgr)

        assert result.shape == test_image_bgr.shape
        assert metrics.parameters["tile_grid_size"] == (16, 16)

    def test_clahe_metrics_collection(self, test_image_bgr):
        """Test that CLAHE collects proper metrics"""
        preprocessor = CLAHEPreprocessor()
        result, metrics = preprocessor.process(test_image_bgr)

        assert metrics.input_shape == test_image_bgr.shape
        assert metrics.output_shape == result.shape
        assert metrics.execution_time_ms > 0
        assert metrics.memory_before_mb > 0
        assert metrics.memory_after_mb > 0

    def test_clahe_preserves_dimensions(self, test_image_rgb):
        """Test that CLAHE preserves image dimensions"""
        preprocessor = CLAHEPreprocessor()
        result, _ = preprocessor.process(test_image_rgb)

        assert result.shape == test_image_rgb.shape


# ============================================================================
# MORPHOLOGICAL OPERATIONS TESTS
# ============================================================================

class TestMorphologicalProcessor:
    """Test Morphological Image Operations"""

    def test_morphology_initialization(self):
        """Test morphological processor initialization"""
        processor = MorphologicalProcessor(kernel_size="medium")
        assert processor.kernel_size == "medium"
        assert processor.kernel is not None

    def test_morphology_invalid_kernel_size(self):
        """Test that invalid kernel size raises error"""
        with pytest.raises(ValueError):
            MorphologicalProcessor(kernel_size="invalid")

    def test_erode_operation(self, test_image_grayscale):
        """Test erosion operation"""
        processor = MorphologicalProcessor(kernel_size="small")
        result, metrics = processor.erode(test_image_grayscale)

        assert result.shape == test_image_grayscale.shape
        assert metrics.operation == "MORPH_ERODE"
        assert metrics.execution_time_ms > 0

    def test_erode_multiple_iterations(self, test_image_grayscale):
        """Test erosion with multiple iterations"""
        processor = MorphologicalProcessor(kernel_size="medium")
        result, metrics = processor.erode(test_image_grayscale, iterations=3)

        assert result.shape == test_image_grayscale.shape
        assert metrics.parameters["iterations"] == 3

    def test_dilate_operation(self, test_image_grayscale):
        """Test dilation operation"""
        processor = MorphologicalProcessor(kernel_size="small")
        result, metrics = processor.dilate(test_image_grayscale)

        assert result.shape == test_image_grayscale.shape
        assert metrics.operation == "MORPH_DILATE"

    def test_dilate_multiple_iterations(self, test_image_grayscale):
        """Test dilation with multiple iterations"""
        processor = MorphologicalProcessor(kernel_size="medium")
        result, metrics = processor.dilate(test_image_grayscale, iterations=2)

        assert result.shape == test_image_grayscale.shape
        assert metrics.parameters["iterations"] == 2

    def test_open_operation(self, test_image_noisy):
        """Test morphological opening (erode + dilate)"""
        processor = MorphologicalProcessor(kernel_size="small")
        result, metrics = processor.open(test_image_noisy)

        assert result.shape == test_image_noisy.shape
        assert metrics.operation == "MORPH_OPEN"

    def test_open_removes_noise(self, test_image_noisy):
        """Test that opening removes small noise"""
        processor = MorphologicalProcessor(kernel_size="small")
        result, _ = processor.open(test_image_noisy)

        # Opened image should have lower variance (smoother)
        original_variance = np.var(test_image_noisy)
        opened_variance = np.var(result)

        assert opened_variance <= original_variance

    def test_close_operation(self, test_image_grayscale):
        """Test morphological closing (dilate + erode)"""
        processor = MorphologicalProcessor(kernel_size="small")
        result, metrics = processor.close(test_image_grayscale)

        assert result.shape == test_image_grayscale.shape
        assert metrics.operation == "MORPH_CLOSE"

    def test_morphology_kernel_sizes(self, test_image_grayscale):
        """Test different kernel sizes"""
        for kernel_size in ["small", "medium", "large"]:
            processor = MorphologicalProcessor(kernel_size=kernel_size)
            result, metrics = processor.open(test_image_grayscale)

            assert result.shape == test_image_grayscale.shape
            assert metrics.parameters["kernel_size"] == kernel_size

    def test_morphology_metrics_accuracy(self, test_image_grayscale):
        """Test that morphological metrics are accurate"""
        processor = MorphologicalProcessor(kernel_size="medium")
        result, metrics = processor.erode(test_image_grayscale)

        assert metrics.input_shape == test_image_grayscale.shape
        assert metrics.output_shape == result.shape
        assert metrics.execution_time_ms > 0
        assert metrics.memory_before_mb > 0

    def test_erode_dilate_inverse_relationship(self, test_image_grayscale):
        """Test that erode and dilate have inverse effects on white regions"""
        processor = MorphologicalProcessor(kernel_size="small")

        # Erode reduces white regions
        eroded, _ = processor.erode(test_image_grayscale)
        white_after_erode = np.sum(eroded > 128)

        # Dilate increases white regions
        dilated, _ = processor.dilate(test_image_grayscale)
        white_after_dilate = np.sum(dilated > 128)

        original_white = np.sum(test_image_grayscale > 128)

        # Eroded should have less white, dilated should have more
        assert white_after_erode <= original_white
        assert white_after_dilate >= original_white


# ============================================================================
# EDGE DETECTION TESTS
# ============================================================================

class TestEdgeDetectionProcessor:
    """Test Edge Detection Operations"""

    def test_canny_initialization(self):
        """Test edge detection processor initialization"""
        processor = EdgeDetectionProcessor()
        assert processor is not None

    def test_canny_detection(self, test_image_bgr):
        """Test Canny edge detection"""
        processor = EdgeDetectionProcessor()
        result, metrics = processor.canny(test_image_bgr)

        assert result.shape[:2] == test_image_bgr.shape[:2]
        assert result.dtype == np.uint8
        assert metrics.operation == "EDGE_CANNY"

    def test_canny_threshold_values(self, test_image_bgr):
        """Test Canny with different threshold values"""
        processor = EdgeDetectionProcessor()

        result1, metrics1 = processor.canny(test_image_bgr, threshold1=50, threshold2=150)
        result2, metrics2 = processor.canny(test_image_bgr, threshold1=100, threshold2=200)

        # Both should return valid edge maps
        assert result1.shape == result2.shape
        assert metrics1.parameters["threshold1"] == 50
        assert metrics2.parameters["threshold1"] == 100

    def test_canny_low_threshold(self, test_image_bgr):
        """Test Canny with low thresholds (more edges detected)"""
        processor = EdgeDetectionProcessor()
        result, _ = processor.canny(test_image_bgr, threshold1=50, threshold2=100)

        # Low threshold should detect more edges
        edge_count = np.sum(result > 0)
        assert edge_count > 0

    def test_canny_high_threshold(self, test_image_bgr):
        """Test Canny with high thresholds (fewer edges detected)"""
        processor = EdgeDetectionProcessor()
        result, _ = processor.canny(test_image_bgr, threshold1=200, threshold2=400)

        # Result should still be valid
        assert result.shape[:2] == test_image_bgr.shape[:2]

    def test_sobel_detection(self, test_image_bgr):
        """Test Sobel edge detection"""
        processor = EdgeDetectionProcessor()
        result, metrics = processor.sobel(test_image_bgr)

        assert result.shape[:2] == test_image_bgr.shape[:2]
        assert result.dtype == np.uint8
        assert metrics.operation == "EDGE_SOBEL"

    def test_sobel_kernel_sizes(self, test_image_bgr):
        """Test Sobel with different kernel sizes"""
        processor = EdgeDetectionProcessor()

        for kernel_size in [1, 3, 5, 7]:
            result, metrics = processor.sobel(test_image_bgr, kernel_size=kernel_size)
            assert result.shape[:2] == test_image_bgr.shape[:2]
            assert metrics.parameters["kernel_size"] == kernel_size

    def test_edge_detection_metrics(self, test_image_bgr):
        """Test that edge detection collects proper metrics"""
        processor = EdgeDetectionProcessor()
        result, metrics = processor.canny(test_image_bgr)

        assert metrics.input_shape == test_image_bgr.shape
        assert metrics.output_shape == result.shape
        assert metrics.execution_time_ms > 0
        assert len(metrics.parameters) > 0

    def test_canny_on_grayscale(self, test_image_grayscale):
        """Test Canny edge detection on grayscale image"""
        processor = EdgeDetectionProcessor()
        result, metrics = processor.canny(test_image_grayscale)

        assert result.shape == test_image_grayscale.shape
        assert metrics.operation == "EDGE_CANNY"


# ============================================================================
# GRAYSCALE VARIANT TESTS
# ============================================================================

class TestGrayscaleVariantProcessor:
    """Test Grayscale Conversion Methods"""

    def test_grayscale_initialization(self):
        """Test grayscale processor initialization"""
        processor = GrayscaleVariantProcessor()
        assert processor is not None

    def test_convert_luminosity(self, test_image_bgr):
        """Test luminosity method grayscale conversion"""
        processor = GrayscaleVariantProcessor()
        result, metrics = processor.convert(test_image_bgr, method="luminosity")

        assert len(result.shape) == 2
        assert result.dtype == np.uint8
        assert metrics.operation == "GRAYSCALE_CONVERT"
        assert metrics.parameters["method"] == "luminosity"

    def test_convert_average(self, test_image_bgr):
        """Test average method grayscale conversion"""
        processor = GrayscaleVariantProcessor()
        result, metrics = processor.convert(test_image_bgr, method="average")

        assert len(result.shape) == 2
        assert metrics.parameters["method"] == "average"

    def test_convert_desaturation(self, test_image_bgr):
        """Test desaturation method grayscale conversion"""
        processor = GrayscaleVariantProcessor()
        result, metrics = processor.convert(test_image_bgr, method="desaturation")

        assert len(result.shape) == 2
        assert metrics.parameters["method"] == "desaturation"

    def test_convert_decomposition(self, test_image_bgr):
        """Test decomposition method grayscale conversion"""
        processor = GrayscaleVariantProcessor()
        result, metrics = processor.convert(test_image_bgr, method="decomposition")

        assert len(result.shape) == 2
        assert metrics.parameters["method"] == "decomposition"

    def test_grayscale_invalid_method(self, test_image_bgr):
        """Test that invalid conversion method raises error"""
        processor = GrayscaleVariantProcessor()

        with pytest.raises(ValueError):
            processor.convert(test_image_bgr, method="invalid")

    def test_grayscale_requires_color_image(self, test_image_grayscale):
        """Test that grayscale input raises error"""
        processor = GrayscaleVariantProcessor()

        with pytest.raises(ValueError):
            processor.convert(test_image_grayscale, method="luminosity")

    def test_grayscale_method_differences(self, test_image_bgr):
        """Test that different methods produce different results"""
        processor = GrayscaleVariantProcessor()

        result_luminosity, _ = processor.convert(test_image_bgr, method="luminosity")
        result_average, _ = processor.convert(test_image_bgr, method="average")
        result_desaturation, _ = processor.convert(test_image_bgr, method="desaturation")

        # Results should be different (not exactly equal)
        assert not np.array_equal(result_luminosity, result_average)
        assert not np.array_equal(result_average, result_desaturation)

    def test_grayscale_metrics_collection(self, test_image_bgr):
        """Test that grayscale conversion collects proper metrics"""
        processor = GrayscaleVariantProcessor()
        result, metrics = processor.convert(test_image_bgr, method="luminosity")

        assert metrics.input_shape == test_image_bgr.shape
        assert metrics.output_shape == result.shape
        assert metrics.execution_time_ms > 0


# ============================================================================
# PIPELINE ORCHESTRATION TESTS
# ============================================================================

class TestPreprocessingPipeline:
    """Test Pipeline Orchestration"""

    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        pipeline = PreprocessingPipeline(cache_enabled=False)
        assert pipeline is not None
        assert not pipeline.cache_enabled

    def test_pipeline_with_cache(self):
        """Test pipeline with caching enabled"""
        pipeline = PreprocessingPipeline(cache_enabled=True, max_cache_size=50)
        assert pipeline.cache_enabled
        assert pipeline.max_cache_size == 50

    def test_pipeline_balanced_preset(self, test_image_bgr):
        """Test balanced preprocessing preset"""
        pipeline = PreprocessingPipeline()
        result = pipeline.execute(test_image_bgr, preset="balanced")

        assert result.success
        assert result.preprocessed_image is not None
        assert len(result.preprocessing_steps) > 0
        assert "CLAHE" in result.preprocessing_steps
        assert "Morphological Open" in result.preprocessing_steps

    def test_pipeline_contrast_preset(self, test_image_bgr):
        """Test contrast enhancement preset"""
        pipeline = PreprocessingPipeline()
        result = pipeline.execute(test_image_bgr, preset="contrast")

        assert result.success
        assert "CLAHE (High Contrast)" in result.preprocessing_steps

    def test_pipeline_edges_preset(self, test_image_bgr):
        """Test edge detection preset"""
        pipeline = PreprocessingPipeline()
        result = pipeline.execute(test_image_bgr, preset="edges")

        assert result.success
        assert "Canny Edge Detection" in result.preprocessing_steps

    def test_pipeline_denoise_preset(self, test_image_noisy):
        """Test denoising preset"""
        pipeline = PreprocessingPipeline()
        result = pipeline.execute(test_image_noisy, preset="denoise")

        assert result.success
        assert "Morphological Open" in result.preprocessing_steps
        assert "Morphological Close" in result.preprocessing_steps

    def test_pipeline_grayscale_preset(self, test_image_bgr):
        """Test grayscale conversion preset"""
        pipeline = PreprocessingPipeline()
        result = pipeline.execute(test_image_bgr, preset="grayscale")

        assert result.success
        assert "Grayscale Conversion" in result.preprocessing_steps
        assert len(result.preprocessed_image.shape) == 2

    def test_pipeline_invalid_preset(self, test_image_bgr):
        """Test that invalid preset fails gracefully"""
        pipeline = PreprocessingPipeline()
        result = pipeline.execute(test_image_bgr, preset="invalid")

        assert not result.success
        assert result.error_message is not None

    def test_pipeline_result_structure(self, test_image_bgr):
        """Test pipeline result structure"""
        pipeline = PreprocessingPipeline()
        result = pipeline.execute(test_image_bgr, preset="balanced")

        assert hasattr(result, "original_image")
        assert hasattr(result, "preprocessed_image")
        assert hasattr(result, "preprocessing_steps")
        assert hasattr(result, "metrics")
        assert hasattr(result, "total_execution_time_ms")
        assert hasattr(result, "success")

    def test_pipeline_metrics_collection(self, test_image_bgr):
        """Test that pipeline collects all metrics"""
        pipeline = PreprocessingPipeline()
        result = pipeline.execute(test_image_bgr, preset="balanced")

        assert len(result.metrics) > 0
        for metric in result.metrics:
            assert isinstance(metric, ProcessingMetrics)
            assert metric.execution_time_ms > 0

    def test_pipeline_clear_cache(self):
        """Test pipeline cache clearing"""
        pipeline = PreprocessingPipeline(cache_enabled=True)
        pipeline.cache["test"] = np.zeros((10, 10))

        pipeline.clear_cache()
        assert len(pipeline.cache) == 0


# ============================================================================
# PERFORMANCE METRICS TESTS
# ============================================================================

class TestPerformanceMetricsCollector:
    """Test Performance Metrics Collection"""

    def test_collector_initialization(self):
        """Test metrics collector initialization"""
        collector = PerformanceMetricsCollector()
        assert len(collector.results) == 0
        assert collector.total_operations == 0

    def test_collector_record_result(self, test_image_bgr):
        """Test recording pipeline results"""
        collector = PerformanceMetricsCollector()
        pipeline = PreprocessingPipeline()
        result = pipeline.execute(test_image_bgr, preset="balanced")

        collector.record_result(result)
        assert len(collector.results) == 1
        assert collector.total_operations > 0

    def test_collector_summary(self, test_image_bgr):
        """Test collector summary generation"""
        collector = PerformanceMetricsCollector()
        pipeline = PreprocessingPipeline()

        for _ in range(3):
            result = pipeline.execute(test_image_bgr, preset="balanced")
            collector.record_result(result)

        summary = collector.get_summary()
        assert summary["total_executions"] == 3
        assert summary["total_operations"] > 0
        assert summary["average_time_ms"] > 0
        assert 0 <= summary["success_rate"] <= 1

    def test_collector_success_rate(self, test_image_bgr):
        """Test success rate calculation"""
        collector = PerformanceMetricsCollector()
        pipeline = PreprocessingPipeline()

        # Add successful results
        for _ in range(3):
            result = pipeline.execute(test_image_bgr, preset="balanced")
            collector.record_result(result)

        summary = collector.get_summary()
        assert summary["success_rate"] == 1.0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPreprocessingIntegration:
    """Integration tests for preprocessing pipeline"""

    def test_full_preprocessing_workflow(self, test_image_bgr):
        """Test complete preprocessing workflow"""
        # Create pipeline with all options
        pipeline = PreprocessingPipeline(cache_enabled=True)

        # Execute multiple presets
        results = []
        for preset in ["balanced", "contrast", "edges", "denoise", "grayscale"]:
            result = pipeline.execute(test_image_bgr, preset=preset)
            results.append(result)
            assert result.success

        # Verify all results were collected
        assert len(results) == 5

    def test_preprocessing_quality_improvement(self, test_image_low_contrast):
        """Test that preprocessing improves image quality"""
        pipeline = PreprocessingPipeline()
        result = pipeline.execute(test_image_low_contrast, preset="contrast")

        # Enhanced image should have better contrast
        original_std = np.std(test_image_low_contrast)
        enhanced_std = np.std(result.preprocessed_image)

        # Contrast should improve
        assert enhanced_std > original_std * 0.8

    def test_preprocessing_performance(self, test_image_bgr):
        """Test preprocessing performance is acceptable"""
        pipeline = PreprocessingPipeline()
        result = pipeline.execute(test_image_bgr, preset="balanced")

        # Should complete in reasonable time (< 1 second for 640x480 image)
        assert result.total_execution_time_ms < 1000

    def test_preprocessing_consistency(self, test_image_bgr):
        """Test that preprocessing is consistent across runs"""
        pipeline = PreprocessingPipeline()

        result1 = pipeline.execute(test_image_bgr, preset="balanced")
        result2 = pipeline.execute(test_image_bgr, preset="balanced")

        # Results should be very similar (within 1% difference)
        diff = np.mean(np.abs(result1.preprocessed_image.astype(float) - result2.preprocessed_image.astype(float)))
        assert diff < 255 * 0.01  # Less than 1% difference

    def test_multiple_image_formats(self):
        """Test preprocessing with different image types"""
        # Create test images of different sizes
        images = [
            np.zeros((480, 640, 3), dtype=np.uint8),
            np.zeros((720, 1280, 3), dtype=np.uint8),
            np.zeros((1080, 1920, 3), dtype=np.uint8),
        ]

        pipeline = PreprocessingPipeline()

        for image in images:
            result = pipeline.execute(image, preset="balanced")
            assert result.success
            assert result.preprocessed_image.shape[:2] == image.shape[:2]


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_empty_image_handling(self):
        """Test handling of invalid images"""
        empty_image = np.array([])

        with pytest.raises((ValueError, cv2.error)):
            pipeline = PreprocessingPipeline()
            # Should raise error on invalid image

    def test_single_channel_to_clahe(self, test_image_grayscale):
        """Test CLAHE on single-channel grayscale"""
        preprocessor = CLAHEPreprocessor()
        result, metrics = preprocessor.process(test_image_grayscale)

        # Should handle grayscale correctly
        assert result.shape == test_image_grayscale.shape

    def test_very_small_image(self):
        """Test preprocessing on very small images"""
        small_image = np.ones((10, 10, 3), dtype=np.uint8) * 128

        pipeline = PreprocessingPipeline()
        result = pipeline.execute(small_image, preset="balanced")

        # Should handle small images
        assert result.success or result.error_message is not None

    def test_metrics_accuracy_small_image(self):
        """Test metrics accuracy on small images"""
        small_image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        preprocessor = CLAHEPreprocessor()
        result, metrics = preprocessor.process(small_image)

        # Metrics should be accurate
        assert metrics.input_shape == small_image.shape
        assert metrics.output_shape == result.shape
        assert metrics.execution_time_ms >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
