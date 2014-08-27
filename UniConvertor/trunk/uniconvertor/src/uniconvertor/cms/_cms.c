/* cms - small package which provides binding to LittleCMS library.
 *
 * Copyright (C) 2009 by Igor E.Novikov
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include <Python.h>
#include <lcms.h>
#include "Imaging.h"

/* redefine the ImagingObject struct defined in _imagingmodule.c */
typedef struct {
    PyObject_HEAD
    Imaging image;
} ImagingObject;

DWORD
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

  else {
    return TYPE_GRAY_8;
  }
}


static PyObject *
pycms_OpenProfile(PyObject *self, PyObject *args) {

	char *profile = NULL;
	cmsHPROFILE hProfile;

	if (!PyArg_ParseTuple(args, "s", &profile))
		return NULL;

	cmsErrorAction(LCMS_ERROR_IGNORE);

	hProfile = cmsOpenProfileFromFile(profile, "r");

	if(hProfile==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCObject_FromVoidPtr((void *)hProfile, (void *)cmsCloseProfile));
}

static PyObject *
pycms_CreateRGBProfile(PyObject *self, PyObject *args) {

	cmsHPROFILE hProfile;

	cmsErrorAction(LCMS_ERROR_IGNORE);

	hProfile = cmsCreate_sRGBProfile();

	if(hProfile==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCObject_FromVoidPtr((void *)hProfile, (void *)cmsCloseProfile));
}

static PyObject *
pycms_CreateLabProfile(PyObject *self, PyObject *args) {

	cmsHPROFILE hProfile;

	cmsErrorAction(LCMS_ERROR_IGNORE);

	hProfile = cmsCreateLabProfile(NULL);

	if(hProfile==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCObject_FromVoidPtr((void *)hProfile, (void *)cmsCloseProfile));
}

static PyObject *
pycms_CreateGrayProfile(PyObject *self, PyObject *args) {

	cmsHPROFILE hProfile;
	LPGAMMATABLE gamma;

	cmsErrorAction(LCMS_ERROR_IGNORE);

	gamma = cmsBuildGamma(256, 2.2);
	hProfile = cmsCreateGrayProfile(cmsD50_xyY(), gamma);
	cmsFreeGamma(gamma);

	if(hProfile==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCObject_FromVoidPtr((void *)hProfile, (void *)cmsCloseProfile));
}

static PyObject *
pycms_BuildTransform (PyObject *self, PyObject *args) {

	char *inMode;
	char *outMode;
	int renderingIntent;
	int inFlags;
	DWORD flags;
	void *inputProfile;
	void *outputProfile;
	cmsHPROFILE hInputProfile, hOutputProfile;
	cmsHTRANSFORM hTransform;

	if (!PyArg_ParseTuple(args, "OsOsii", &inputProfile, &inMode, &outputProfile, &outMode, &renderingIntent, &inFlags)) {
		return NULL;
	}

	cmsErrorAction(LCMS_ERROR_IGNORE);

	hInputProfile = (cmsHPROFILE) PyCObject_AsVoidPtr(inputProfile);
	hOutputProfile = (cmsHPROFILE) PyCObject_AsVoidPtr(outputProfile);
	flags = (DWORD) inFlags;

	hTransform = cmsCreateTransform(hInputProfile, getLCMStype(inMode),
			hOutputProfile, getLCMStype(outMode), renderingIntent, flags);

	if(hTransform==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCObject_FromVoidPtr((void *)hTransform, (void *)cmsDeleteTransform));
}

static PyObject *
pycms_BuildProofingTransform (PyObject *self, PyObject *args) {

	char *inMode;
	char *outMode;
	int renderingIntent;
	int proofingIntent;
	int inFlags;
	DWORD flags;
	void *inputProfile;
	void *outputProfile;
	void *proofingProfile;

	cmsHPROFILE hInputProfile, hOutputProfile, hProofingProfile;
	cmsHTRANSFORM hTransform;

	if (!PyArg_ParseTuple(args, "OsOsOiii", &inputProfile, &inMode, &outputProfile, &outMode,
			&proofingProfile, &renderingIntent, &proofingIntent, &inFlags)) {
		return NULL;
	}

	cmsErrorAction(LCMS_ERROR_IGNORE);

	hInputProfile = (cmsHPROFILE) PyCObject_AsVoidPtr(inputProfile);
	hOutputProfile = (cmsHPROFILE) PyCObject_AsVoidPtr(outputProfile);
	hProofingProfile = (cmsHPROFILE) PyCObject_AsVoidPtr(proofingProfile);
	flags = (DWORD) inFlags;

	hTransform = cmsCreateProofingTransform(hInputProfile, getLCMStype(inMode),
			hOutputProfile, getLCMStype(outMode), hProofingProfile, renderingIntent, proofingIntent, flags);

	if(hTransform==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("O", PyCObject_FromVoidPtr((void *)hTransform, (void *)cmsDeleteTransform));
}

static PyObject *
pycms_SetAlarmCodes (PyObject *self, PyObject *args) {

	int red, green, blue;

	if (!PyArg_ParseTuple(args, "iii", &red, &green, &blue)) {
		return NULL;
	}

	cmsSetAlarmCodes(red, green, blue);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
pycms_TransformPixel (PyObject *self, PyObject *args) {

	unsigned char *inbuf;
	int channel1,channel2,channel3,channel4;
	void *transform;
	cmsHTRANSFORM hTransform;
	PyObject *result;

	if (!PyArg_ParseTuple(args, "Oiiii", &transform, &channel1, &channel2, &channel3, &channel4)) {
		return NULL;
	}

	cmsErrorAction(LCMS_ERROR_IGNORE);

	inbuf=malloc(4);
	inbuf[0]=(unsigned char)channel1;
	inbuf[1]=(unsigned char)channel2;
	inbuf[2]=(unsigned char)channel3;
	inbuf[3]=(unsigned char)channel4;

	hTransform = (cmsHTRANSFORM) PyCObject_AsVoidPtr(transform);

	cmsDoTransform(hTransform, inbuf, inbuf, 1);

	result = Py_BuildValue("[iiii]", inbuf[0], inbuf[1], inbuf[2], inbuf[3]);
	free(inbuf);
	return result;
}


static PyObject *
pycms_TransformPixel2 (PyObject *self, PyObject *args) {

	double channel1,channel2,channel3,channel4;
	unsigned char *inbuf;
	void *transform;
	cmsHTRANSFORM hTransform;
	PyObject *result;

	if (!PyArg_ParseTuple(args, "Odddd", &transform, &channel1, &channel2, &channel3, &channel4)) {
		return NULL;
	}

	cmsErrorAction(LCMS_ERROR_IGNORE);

	inbuf=malloc(4);
	inbuf[0]=(unsigned char)(channel1*255);
	inbuf[1]=(unsigned char)(channel2*255);
	inbuf[2]=(unsigned char)(channel3*255);
	inbuf[3]=(unsigned char)(channel4*255);

	hTransform = (cmsHTRANSFORM) PyCObject_AsVoidPtr(transform);

	cmsDoTransform(hTransform, inbuf, inbuf, 1);

	result = Py_BuildValue("(dddd)", (double)inbuf[0]/255, (double)inbuf[1]/255,
			(double)inbuf[2]/255, (double)inbuf[3]/255);

	free(inbuf);
	return result;
}

static PyObject *
pycms_TransformBitmap (PyObject *self, PyObject *args) {

	ImagingObject* inImage;
	ImagingObject* outImage;
	Imaging inImg, outImg;
	void *transform;
	cmsHTRANSFORM hTransform;
	int width, height, i;

	if (!PyArg_ParseTuple(args, "OOOii", &transform, &inImage, &outImage, &width, &height)) {
		return NULL;
	}

	cmsErrorAction(LCMS_ERROR_IGNORE);

	inImg=inImage->image;
	outImg=outImage->image;

	hTransform = (cmsHTRANSFORM) PyCObject_AsVoidPtr(transform);

	for (i = 0; i < height; i++) {
		cmsDoTransform(hTransform, inImg->image[i],	outImg->image[i], width);
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
pycms_GetProfileName (PyObject *self, PyObject *args) {

	void *profile;
	cmsHPROFILE hProfile;

	if (!PyArg_ParseTuple(args, "O", &profile)) {
		return NULL;
	}

	cmsErrorAction(LCMS_ERROR_IGNORE);

	hProfile = (cmsHPROFILE) PyCObject_AsVoidPtr(profile);

	return Py_BuildValue("s", cmsTakeProductDesc(hProfile));
}

static PyObject *
pycms_GetProfileInfo (PyObject *self, PyObject *args) {

	void *profile;
	cmsHPROFILE hProfile;

	if (!PyArg_ParseTuple(args, "O", &profile)) {
		return NULL;
	}

	cmsErrorAction(LCMS_ERROR_IGNORE);

	hProfile = (cmsHPROFILE) PyCObject_AsVoidPtr(profile);

	return Py_BuildValue("s", cmsTakeProductName(hProfile));
}

static PyObject *
pycms_GetPixelsFromImage (PyObject *self, PyObject *args) {

	int width, height, bytes_per_pixel, i;
	unsigned char *pixbuf;
	ImagingObject* inImage;
	Imaging inImg;

	if (!PyArg_ParseTuple(args, "Oiii", &inImage, &width, &height, &bytes_per_pixel)) {
		return NULL;
	}

	pixbuf=malloc(width*height*bytes_per_pixel);
	inImg=inImage->image;

	for (i = 0; i < height; i++) {
		memcpy(&pixbuf[i*width*bytes_per_pixel], inImg->image[i], width*bytes_per_pixel);
	}

	return Py_BuildValue("O", PyCObject_FromVoidPtr((void *)pixbuf, (void *)free));
}

static PyObject *
pycms_SetImagePixels (PyObject *self, PyObject *args) {

	int width, height, bytes_per_pixel, i;
	void *pixels;
	unsigned char *pixbuf;
	ImagingObject* inImage;
	Imaging inImg;

	if (!PyArg_ParseTuple(args, "OOiii", &pixels, &inImage, &width, &height, &bytes_per_pixel)) {
		return NULL;
	}

	pixbuf = (unsigned char *) PyCObject_AsVoidPtr(pixels);
	inImg=inImage->image;

	for (i = 0; i < height; i++) {
		memcpy(inImg->image[i], &pixbuf[i*width*bytes_per_pixel], width*bytes_per_pixel);
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
pycms_TransformPixels (PyObject *self, PyObject *args) {

	int width;
	unsigned char *pixbuf;
	unsigned char *result;
	void *pixels;
	void *transform;
	cmsHTRANSFORM hTransform;

	if (!PyArg_ParseTuple(args, "OOi", &transform, &pixels, &width)) {
		return NULL;
	}

	cmsErrorAction(LCMS_ERROR_IGNORE);

	hTransform = (cmsHTRANSFORM) PyCObject_AsVoidPtr(transform);
	pixbuf = (unsigned char *) PyCObject_AsVoidPtr(pixels);
	result=malloc(width*4);

	cmsDoTransform(hTransform, pixbuf, result, width);

	return Py_BuildValue("O",  PyCObject_FromVoidPtr((void *)result, (void *)free));
}

static
PyMethodDef pycms_methods[] = {
	{"openProfile", pycms_OpenProfile, METH_VARARGS},
	{"createRGBProfile", pycms_CreateRGBProfile, METH_VARARGS},
	{"createLabProfile", pycms_CreateLabProfile, METH_VARARGS},
	{"createGrayProfile", pycms_CreateGrayProfile, METH_VARARGS},
	{"buildTransform", pycms_BuildTransform, METH_VARARGS},
	{"buildProofingTransform", pycms_BuildProofingTransform, METH_VARARGS},
	{"setAlarmCodes", pycms_SetAlarmCodes, METH_VARARGS},
	{"transformPixel", pycms_TransformPixel, METH_VARARGS},
	{"transformPixel2", pycms_TransformPixel2, METH_VARARGS},
	{"transformBitmap", pycms_TransformBitmap, METH_VARARGS},
	{"getProfileName", pycms_GetProfileName, METH_VARARGS},
	{"getProfileInfo", pycms_GetProfileInfo, METH_VARARGS},
	{"getPixelsFromImage", pycms_GetPixelsFromImage, METH_VARARGS},
	{"setImagePixels", pycms_SetImagePixels, METH_VARARGS},
	{"transformPixels", pycms_TransformPixels, METH_VARARGS},
	{NULL, NULL}
};

void
init_cms(void)
{
    Py_InitModule("_cms", pycms_methods);
}
