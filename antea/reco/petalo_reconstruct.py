from ctypes import *
import numpy as np

class PetaloReconstructor:
    """
    Python wrapper class to perform reconstruction in PETALO. The class
    provides a method to call the C-based reconstruction using the
    configuration provided by the class variables.

    **NOTE:** the LOR points may need to be sorted for the reconstruction to
    be correct
    """

    def __init__(self, niterations = 1, TOF_resolution = 200,
                 img_size_xy = 180.0, img_size_z = 180.0, img_nvoxels_xy = 60,
                 img_nvoxels_z = 60, libdir = "anteacpp/libPETALO.so"):

        # Set default values for key variables.
        self.nlines = 1
        self.niterations = niterations
        self.TOF = True
        self.TOF_resolution = TOF_resolution
        self.img_size_xy = img_size_xy
        self.img_size_z = img_size_z
        self.img_nvoxels_xy = img_nvoxels_xy
        self.img_nvoxels_z = img_nvoxels_z

        # Load the C library.
        self.lib = cdll.LoadLibrary(libdir)

    def reconstruct(self, lor_x1, lor_y1, lor_z1, lor_t1,
                    lor_x2, lor_y2, lor_z2, lor_t2):
        """
        Performs reconstruction by calling a C-implemented function. The
        reconstruction is list-mode, so the inputs are the coordinates
        :math:`(x,y,z,t)` for each line of response (LOR). These coordinates
        are specified as separate lists.

        :param lor_x1: x-coordinates for the first point in the LOR
        :type lor_x1: list
        :param lor_y1: y-coordinates for the first point in the LOR
        :type lor_y1: list
        :param lor_z1: y-coordinates for the first point in the LOR
        :type lor_z1: list
        :param lor_t1: time coordinates for the first point in the LOR
        :type lor_t1: list
        :param lor_x2: x-coordinates for the second point in the LOR
        :type lor_x2: list
        :param lor_y2: y-coordinates for the second point in the LOR
        :type lor_y2: list
        :param lor_z2: y-coordinates for the second point in the LOR
        :type lor_z2: list
        :param lor_t2: time coordinates for the second point in the LOR
        :type lor_t2: list
        :returns: array of shape [`img_size_xy`, `img_size_xy`,`img_size_z`] containing the reconstructed image
        :rtype: numpy.ndarray
        """

        # Ensure arrays are all the same size.
        ncoinc = len(lor_x1)
        if(len(lor_y1) != ncoinc or len(lor_z1) != ncoinc
           or len(lor_t1) != ncoinc or len(lor_x2) != ncoinc
           or len(lor_y2) != ncoinc or len(lor_z2) != ncoinc
           or len(lor_t2) != ncoinc):
            print("ERROR: all LOR arrays must contain the same # of values")

        # ---------------------------------------------------------
        # Call the C-function for reconstruction.
        # ---------------------------------------------------------

        # Create C-arrays
        lor_x1 = (c_float * ncoinc)(*lor_x1)
        lor_y1 = (c_float * ncoinc)(*lor_y1)
        lor_z1 = (c_float * ncoinc)(*lor_z1)
        lor_t1 = (c_float * ncoinc)(*lor_t1)
        lor_x2 = (c_float * ncoinc)(*lor_x2)
        lor_y2 = (c_float * ncoinc)(*lor_y2)
        lor_z2 = (c_float * ncoinc)(*lor_z2)
        lor_t2 = (c_float * ncoinc)(*lor_t2)

        # Set the argument types and return type.
        self.lib.MLEM_TOF_Reco.argtypes = (c_int, c_int, c_bool, c_float,
         c_float, c_float, c_int, c_int, c_int,
         POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float),
         POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float))

        self.lib.MLEM_TOF_Reco.restype = POINTER(c_float)

        # Call the function.
        img = self.lib.MLEM_TOF_Reco(self.nlines, self.niterations, self.TOF,
                                self.TOF_resolution, self.img_size_xy,
                                self.img_size_z, self.img_nvoxels_xy,
                                self.img_nvoxels_z, ncoinc,
                                lor_x1, lor_y1, lor_z1, lor_t1,
                                lor_x2, lor_y2, lor_z2, lor_t2)

        # --------------------------------------------------
        # Prepare the numpy image from the C float pointer.
        # --------------------------------------------------

        # Construct some quantities for ease of use later.
        xdim = ydim = self.img_nvoxels_xy
        zdim = self.img_nvoxels_z
        nvoxels = xdim*ydim*zdim

        # Create a 3D numpy array of the correct dimensions.
        img_arr = np.zeros([xdim,ydim,zdim])

        # Extract the information from the C array into a 1D numpy array.
        rimg = np.array([img[i] for i in range(nvoxels)])

        # Fill the final 3D image, extracting the voxel indices from the
        #  single index in the 1D array.
        for ivox,w in enumerate(rimg):
            i = int(ivox % xdim)
            j = int(ivox / xdim) % ydim
            k = int(ivox / (xdim*ydim))
            img_arr[i,j,k] = w

        return img_arr
