import os

os.environ["PYOPENGL_PLATFORM"] = "egl" # Get PyOpenGL to use EGL/GLES

#import OpenGL.GLES2 as gl
#import OpenGL.EGL as egl
#from OpenGL import arrays

# Now fix stupid missing imports in PyOpenGL GLES support...
import OpenGL.GLES2.VERSION.GLES2_2_0 as gl2
from OpenGL._bytes import _NULL_8_BYTE
from OpenGL.arrays.arraydatatype import ArrayDatatype
from OpenGL import contextdata
gl2._NULL_8_BYTE = _NULL_8_BYTE
gl2.ArrayDatatype = ArrayDatatype
gl2.contextdata = contextdata
del gl2, _NULL_8_BYTE, ArrayDatatype, contextdata
