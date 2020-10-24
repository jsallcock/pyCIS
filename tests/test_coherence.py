import unittest
import numpy as np
from numpy.testing import assert_almost_equal
import xarray as xr
from scipy.constants import c, atomic_mass, e
from pycis.model import calculate_coherence


class TestCoherence(unittest.TestCase):
    def test_gaussian_multiplet(self, ):
        """
        Test that the correct coherence is returned for a simple spectral lineshape for which an analytical result
        exists.

        """

        # define spectrum (corresponds to Doppler-broadened carbon III triplet at 464.9 nm):
        wls = np.array([464.742e-9, 465.025e-9, 465.147e-9, ])  # line component centre wavelengths in m
        rel_ints = np.array([0.556, 0.333, 0.111, ])  # relative intensities
        freq_com = (c / wls * rel_ints).sum()  # centre-of-mass frequency in Hz
        temperature = 15  # in eV
        sigma_freq = freq_com / c * np.sqrt(temperature * e / (12 * atomic_mass))  # line Doppler-width st. dev. in Hz

        n_sigma = 30  # extent of coordinate grid
        n_bins = 10000
        kappa_0 = 1  # this is a non-dispersive test
        delay = (0.5 - np.random.rand(10)) * 4e4  # randomly generate interferometer delays (in rad)
        delay = xr.DataArray(delay, dims=('delay_0',), coords=(delay, ), attrs={'units': 'rad'})

        freq = np.linspace(freq_com - n_sigma * sigma_freq, freq_com + n_sigma * sigma_freq, n_bins)
        freq = xr.DataArray(freq, dims=('frequency',), coords=(freq,), attrs={'units': 'Hz'})

        # define area-normalised Gaussian function for frequency f
        def gaussian(f, f_0, sigma):
            """
            f is frequency, f_0 is centre-frequency and sigma is standard deviation, all in Hz
            """
            return 1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(- 1 / 2 * ((f - f_0) / sigma) ** 2)

        # define degree of coherence (DOC) of an area-normalised Gaussian function for delay d
        def doc_gaussian(d, f_0, sigma):
            """
            d is delay in rad, f_0 is centre-frequency and sigma is standard deviation, both in Hz
            """
            s = 1 + (f_0 - freq_com) / freq_com
            return np.exp(-2 * (np.pi * sigma * (d / (2 * np.pi * freq_com)) * kappa_0) ** 2) * np.exp(1j * d * s)

        spectrum = 0
        doc_analytical = 0
        for wl, rel_int in zip(wls, rel_ints):
            spectrum += rel_int * gaussian(freq, c / wl, sigma_freq)
            doc_analytical += rel_int * doc_gaussian(delay, c / wl, sigma_freq)

        doc_numerical = calculate_coherence(spectrum, delay, material=None, )

        assert_almost_equal(doc_numerical.real.data, doc_analytical.real.data, )
        assert_almost_equal(doc_numerical.imag.data, doc_analytical.imag.data, )


if __name__ == '__main__':
    unittest.main()
