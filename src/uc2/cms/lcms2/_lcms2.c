/*  _lcms2 - provides binding to LittleCMS library version 2.
 *
 *  Copyright (C) 2011-2020 by Ihor E. Novikov
 *
 * 	This program is free software: you can redistribute it and/or modify
 *	it under the terms of the GNU Affero General Public License
 *	as published by the Free Software Foundation, either version 3
 *	of the License, or (at your option) any later version.
 *
 *	This program is distributed in the hope that it will be useful,
 *	but WITHOUT ANY WARRANTY; without even the implied warranty of
 *	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *	GNU General Public License for more details.
 *
 *	You should have received a copy of the GNU Affero General Public License
 *	along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <lcms2.h>
#include <Imaging.h>

/* redefine the ImagingObject struct defined in _imagingmodule.c */
typedef struct {
    PyObject_HEAD
    Imaging image;
} ImagingObject;

cmsUInt32Number
getLCMStype (char* mode) {

  if (strcmp(mode, "RGB") == 0) {
    return TYPE_RGBA_8;
  }
  else if (strcmp(mode, "RGBA") == 0) {
    return TYPE_RGBA_8;
  }
  else if (strcmp(mode, "RGBX") == 0) {
    return TYPE_RGBA_8;
  }
  else if (strcmp(mode, "RGBA;16B") == 0) {
    return TYPE_RGBA_16;
  }
  else if (strcmp(mode, "CMYK") == 0) {
    return TYPE_CMYK_8;
  }
  else if (strcmp(mode, "L") == 0) {
    return TYPE_GRAY_8;
  }
  else if (strcmp(mode, "L;16") == 0) {
    return TYPE_GRAY_16;
  }
  else if (strcmp(mode, "L;16B") == 0) {
    return TYPE_GRAY_16_SE;
  }
  else if (strcmp(mode, "YCCA") == 0) {
    return TYPE_YCbCr_8;
  }
  else if (strcmp(mode, "YCC") == 0) {
    return TYPE_YCbCr_8;
  }
  else if (strcmp(mode, "LAB") == 0) {
    return TYPE_Lab_8;
  }

  else {
    return TYPE_GRAY_8;
  }
}


static PyObject *
lcms2_OpenProfile(PyObject *self, PyObject *args) {

	char *profile = NULL;
	cmsHPROFILE hProfile;

	if (!PyArg_ParseTuple(args, "s", &profile)){
		Py_INCREF(Py_None);
		return Py_None;
	}

	hProfile = cmsOpenProfileFromFile(profile, "r");

	if(hProfile==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCapsule_New((void *)hProfile, NULL, (void *)cmsCloseProfile));
}

static PyObject *
lcms2_OpenProfileFromBytes(PyObject *self, PyObject *args) {

	Py_ssize_t size;
	char *profile;
	cmsHPROFILE hProfile;

	if (!PyArg_ParseTuple(args, "s#", &profile, &size)){
		Py_INCREF(Py_None);
		return Py_None;
	}

	hProfile = 	cmsOpenProfileFromMem(profile, size);

	if(hProfile==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCapsule_New((void *)hProfile, NULL, (void *)cmsCloseProfile));
}

static PyObject *
lcms2_CreateRGBProfile(PyObject *self, PyObject *args) {

	cmsHPROFILE hProfile;

	hProfile = cmsCreate_sRGBProfile();

	if(hProfile==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCapsule_New((void *)hProfile, NULL, (void *)cmsCloseProfile));
}

static PyObject *
lcms2_CreateLabProfile(PyObject *self, PyObject *args) {

	cmsHPROFILE hProfile;

	hProfile = cmsCreateLab4Profile(0);

	if(hProfile==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCapsule_New((void *)hProfile, NULL, (void *)cmsCloseProfile));
}

static PyObject *
lcms2_CreateGrayProfile(PyObject *self, PyObject *args) {

	cmsHPROFILE hProfile;
	cmsToneCurve *tonecurve;

	tonecurve = cmsBuildGamma(NULL, 2.2);
	hProfile = cmsCreateGrayProfile(0, tonecurve);
	cmsFreeToneCurve(tonecurve);

	if(hProfile==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCapsule_New((void *)hProfile, NULL, (void *)cmsCloseProfile));
}

static PyObject *
lcms2_BuildTransform (PyObject *self, PyObject *args) {

	char *inMode;
	char *outMode;
	int renderingIntent;
	int inFlags;
	cmsUInt32Number flags;
	void *inputProfile;
	void *outputProfile;
	cmsHPROFILE hInputProfile, hOutputProfile;
	cmsHTRANSFORM hTransform;

	if (!PyArg_ParseTuple(args, "OsOsii", &inputProfile, &inMode, &outputProfile, &outMode, &renderingIntent, &inFlags)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	hInputProfile = (cmsHPROFILE) PyCapsule_GetPointer(inputProfile, NULL);
	hOutputProfile = (cmsHPROFILE) PyCapsule_GetPointer(outputProfile, NULL);
	flags = (cmsUInt32Number) inFlags;

	hTransform = cmsCreateTransform(hInputProfile, getLCMStype(inMode),
			hOutputProfile, getLCMStype(outMode), renderingIntent, flags);

	if(hTransform==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCapsule_New((void *)hTransform, NULL, (void *)cmsDeleteTransform));
}

static PyObject *
lcms2_BuildProofingTransform (PyObject *self, PyObject *args) {

	char *inMode;
	char *outMode;
	int renderingIntent;
	int proofingIntent;
	int inFlags;
	cmsUInt32Number flags;
	void *inputProfile;
	void *outputProfile;
	void *proofingProfile;

	cmsHPROFILE hInputProfile, hOutputProfile, hProofingProfile;
	cmsHTRANSFORM hTransform;

	if (!PyArg_ParseTuple(args, "OsOsOiii", &inputProfile, &inMode, &outputProfile, &outMode,
			&proofingProfile, &renderingIntent, &proofingIntent, &inFlags)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	hInputProfile = (cmsHPROFILE) PyCapsule_GetPointer(inputProfile, NULL);
	hOutputProfile = (cmsHPROFILE) PyCapsule_GetPointer(outputProfile, NULL);
	hProofingProfile = (cmsHPROFILE) PyCapsule_GetPointer(proofingProfile, NULL);
	flags = (cmsUInt32Number) inFlags;

	hTransform = cmsCreateProofingTransform(hInputProfile, getLCMStype(inMode),
			hOutputProfile, getLCMStype(outMode), hProofingProfile, renderingIntent, proofingIntent, flags);

	if(hTransform==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCapsule_New((void *)hTransform, NULL, (void *)cmsDeleteTransform));
}

static PyObject *
lcms2_SetAlarmCodes (PyObject *self, PyObject *args) {

	int red, green, blue;
	cmsUInt16Number alarm_codes[cmsMAXCHANNELS] = { 0, };

	if (!PyArg_ParseTuple(args, "iii", &red, &green, &blue)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	alarm_codes[0] = (cmsUInt16Number) red * 256;
	alarm_codes[1] = (cmsUInt16Number) green * 256;
	alarm_codes[2] = (cmsUInt16Number) blue * 256;

	cmsSetAlarmCodes(alarm_codes);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
lcms2_TransformPixel (PyObject *self, PyObject *args) {

	unsigned char *inbuf;
	int channel1,channel2,channel3,channel4;
	void *transform;
	cmsHTRANSFORM hTransform;
	PyObject *result;

	if (!PyArg_ParseTuple(args, "Oiiii", &transform, &channel1, &channel2, &channel3, &channel4)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	inbuf=malloc(4);
	inbuf[0]=(unsigned char)channel1;
	inbuf[1]=(unsigned char)channel2;
	inbuf[2]=(unsigned char)channel3;
	inbuf[3]=(unsigned char)channel4;

	hTransform = (cmsHTRANSFORM) PyCapsule_GetPointer(transform, NULL);

	cmsDoTransform(hTransform, inbuf, inbuf, 1);

	result = Py_BuildValue("[iiii]", inbuf[0], inbuf[1], inbuf[2], inbuf[3]);
	free(inbuf);
	return result;
}


static PyObject *
lcms2_TransformPixel2 (PyObject *self, PyObject *args) {

	double channel1,channel2,channel3,channel4;
	unsigned char *inbuf;
	void *transform;
	cmsHTRANSFORM hTransform;
	PyObject *result;

	if (!PyArg_ParseTuple(args, "Odddd", &transform, &channel1, &channel2, &channel3, &channel4)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	inbuf=malloc(4);
	inbuf[0]=(unsigned char)(channel1*255);
	inbuf[1]=(unsigned char)(channel2*255);
	inbuf[2]=(unsigned char)(channel3*255);
	inbuf[3]=(unsigned char)(channel4*255);

	hTransform = (cmsHTRANSFORM) PyCapsule_GetPointer(transform, NULL);

	cmsDoTransform(hTransform, inbuf, inbuf, 1);

	result = Py_BuildValue("(dddd)", (double)inbuf[0]/255, (double)inbuf[1]/255,
			(double)inbuf[2]/255, (double)inbuf[3]/255);

	free(inbuf);
	return result;
}

static PyObject *
lcms2_TransformBitmap (PyObject *self, PyObject *args) {

	ImagingObject* inImage;
	ImagingObject* outImage;
	Imaging inImg, outImg;
	void *transform;
	cmsHTRANSFORM hTransform;
	int width, height, i;

	if (!PyArg_ParseTuple(args, "OOOii", &transform, &inImage, &outImage, &width, &height)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	inImg=inImage->image;
	outImg=outImage->image;

	hTransform = (cmsHTRANSFORM) PyCapsule_GetPointer(transform, NULL);

	for (i = 0; i < height; i++) {
		cmsDoTransform(hTransform, inImg->image[i],	outImg->image[i], width);
	}

	Py_INCREF(Py_None);
	return Py_None;
}

#define BUFFER_SIZE 1000

static PyObject *
lcms2_GetProfileName (PyObject *self, PyObject *args) {

	void *profile;
	cmsHPROFILE hProfile;
	char *buffer;
	PyObject *ret;

	if (!PyArg_ParseTuple(args, "O", &profile)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	buffer=malloc(BUFFER_SIZE);
	hProfile = (cmsHPROFILE) PyCapsule_GetPointer(profile, NULL);

	cmsGetProfileInfoASCII(hProfile,
			cmsInfoDescription,
			cmsNoLanguage, cmsNoCountry,
			buffer, BUFFER_SIZE);

	ret=Py_BuildValue("y", buffer);
	free(buffer);
	return ret;
}

static PyObject *
lcms2_GetProfileInfo (PyObject *self, PyObject *args) {

	void *profile;
	cmsHPROFILE hProfile;
	char *buffer;
	PyObject *ret;

	if (!PyArg_ParseTuple(args, "O", &profile)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	buffer=malloc(BUFFER_SIZE);
	hProfile = (cmsHPROFILE) PyCapsule_GetPointer(profile, NULL);

	cmsGetProfileInfoASCII(hProfile,
			cmsInfoModel,
			cmsNoLanguage, cmsNoCountry,
			buffer, BUFFER_SIZE);

	ret=Py_BuildValue("y", buffer);
	free(buffer);
	return ret;
}

static PyObject *
lcms2_GetProfileInfoCopyright (PyObject *self, PyObject *args) {

	void *profile;
	cmsHPROFILE hProfile;
	char *buffer;
	PyObject *ret;

	if (!PyArg_ParseTuple(args, "O", &profile)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	buffer=malloc(BUFFER_SIZE);
	hProfile = (cmsHPROFILE) PyCapsule_GetPointer(profile, NULL);

	cmsGetProfileInfoASCII(hProfile,
			cmsInfoCopyright,
			cmsNoLanguage, cmsNoCountry,
			buffer, BUFFER_SIZE);

	ret=Py_BuildValue("y", buffer);
	free(buffer);
	return ret;
}

static PyObject *
lcms2_GetPixelsFromImage (PyObject *self, PyObject *args) {

	int width, height, bytes_per_pixel, i;
	unsigned char *pixbuf;
	ImagingObject* inImage;
	Imaging inImg;

	if (!PyArg_ParseTuple(args, "Oiii", &inImage, &width, &height, &bytes_per_pixel)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	pixbuf=malloc(width*height*bytes_per_pixel);
	inImg=inImage->image;

	for (i = 0; i < height; i++) {
		memcpy(&pixbuf[i*width*bytes_per_pixel], inImg->image[i], width*bytes_per_pixel);
	}

	return Py_BuildValue("O", PyCapsule_New((void *)pixbuf, NULL, (void *)free));
}

static PyObject *
lcms2_SetImagePixels (PyObject *self, PyObject *args) {

	int width, height, bytes_per_pixel, i;
	void *pixels;
	unsigned char *pixbuf;
	ImagingObject* inImage;
	Imaging inImg;

	if (!PyArg_ParseTuple(args, "OOiii", &pixels, &inImage, &width, &height, &bytes_per_pixel)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	pixbuf = (unsigned char *) PyCapsule_GetPointer(pixels, NULL);
	inImg=inImage->image;

	for (i = 0; i < height; i++) {
		memcpy(inImg->image[i], &pixbuf[i*width*bytes_per_pixel], width*bytes_per_pixel);
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
lcms2_TransformPixels (PyObject *self, PyObject *args) {

	int width;
	unsigned char *pixbuf;
	unsigned char *result;
	void *pixels;
	void *transform;
	cmsHTRANSFORM hTransform;

	if (!PyArg_ParseTuple(args, "OOi", &transform, &pixels, &width)) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	hTransform = (cmsHTRANSFORM) PyCapsule_GetPointer(transform, NULL);
	pixbuf = (unsigned char *) PyCapsule_GetPointer(pixels, NULL);
	result=malloc(width*4);

	cmsDoTransform(hTransform, pixbuf, result, width);

	return Py_BuildValue("O",  PyCapsule_New((void *)result, NULL, (void *)free));
}

static PyObject *
lcms2_GetVersion (PyObject *self, PyObject *args) {
	return Py_BuildValue("i",  LCMS_VERSION);
}

//============Module Initialization==============

static
PyMethodDef lcms2_methods[] = {
	{"getVersion", lcms2_GetVersion, METH_VARARGS},
	{"openProfile", lcms2_OpenProfile, METH_VARARGS},
	{"openProfileFromBytes", lcms2_OpenProfileFromBytes, METH_VARARGS},
	{"createRGBProfile", lcms2_CreateRGBProfile, METH_VARARGS},
	{"createLabProfile", lcms2_CreateLabProfile, METH_VARARGS},
	{"createGrayProfile", lcms2_CreateGrayProfile, METH_VARARGS},
	{"buildTransform", lcms2_BuildTransform, METH_VARARGS},
	{"buildProofingTransform", lcms2_BuildProofingTransform, METH_VARARGS},
	{"setAlarmCodes", lcms2_SetAlarmCodes, METH_VARARGS},
	{"transformPixel", lcms2_TransformPixel, METH_VARARGS},
	{"transformPixel2", lcms2_TransformPixel2, METH_VARARGS},
	{"transformBitmap", lcms2_TransformBitmap, METH_VARARGS},
	{"getProfileName", lcms2_GetProfileName, METH_VARARGS},
	{"getProfileInfo", lcms2_GetProfileInfo, METH_VARARGS},
	{"getProfileInfoCopyright", lcms2_GetProfileInfoCopyright, METH_VARARGS},
	{"getPixelsFromImage", lcms2_GetPixelsFromImage, METH_VARARGS},
	{"setImagePixels", lcms2_SetImagePixels, METH_VARARGS},
	{"transformPixels", lcms2_TransformPixels, METH_VARARGS},
	{NULL, NULL}
};

struct module_state {
    PyObject *error;
};

#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))

static int lcms2_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int lcms2_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "_lcms2",
    NULL,
    sizeof(struct module_state),
    lcms2_methods,
    NULL,
    lcms2_traverse,
    lcms2_clear,
    NULL
};

#define INITERROR return NULL

PyMODINIT_FUNC
PyInit__lcms2(void) {
    return PyModule_Create(&moduledef);
}
