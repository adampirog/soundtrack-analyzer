import numpy as np
import pytest

from soundtrack_analyzer.analyze import patch_signal


@pytest.mark.parametrize(
    "signal, patched",
    [
        ([0, 200, 200], [101, 200, 200]),
        ([200, 200, 0], [200, 200, 101]),
        ([200, 0, 0, 0], [200, 0, 0, 0]),
        ([0, 0, 0, 0], [0, 0, 0, 0]),
        ([200, 200, 200, 200], [200, 200, 200, 200]),
        ([0, 0, 200, 0], [101, 101, 200, 101]),
        (
            [0, 200, 200, 0, 0, 0, 200, 0, 200, 0, 0, 200, 200, 0],
            [101, 200, 200, 0, 0, 0, 200, 101, 200, 101, 101, 200, 200, 101],
        ),
        (
            [0, 0, 0, 0, 0, 0, 200, 0, 200, 0, 0, 200, 200, 0],
            [0, 0, 0, 0, 0, 0, 200, 101, 200, 101, 101, 200, 200, 101],
        ),
        (
            [0, 200, 200, 0, 0, 0, 200, 0, 200, 0, 0, 200, 0, 0, 0],
            [101, 200, 200, 0, 0, 0, 200, 101, 200, 101, 101, 200, 0, 0, 0],
        ),
    ],
)
def test_signal_patching(signal: list, patched: list):
    cutoff = 100
    max_gap = 2

    signal = np.array(signal)

    result = patch_signal(signal, cutoff, max_gap)

    assert np.allclose(patched, result)
