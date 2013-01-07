Introduction
============

Provides an image field that can crop, zoom or scale an image instead of just scaling it.
It is fully compatible with archetype's way of defining image sizes and cropped images can be accessed the traversal way ( context/image_[size_name]).

Some cropping or clipping products already exists but I don't think they are flexible enough to cover every need(Products.RichImage, Products.croppingimage, archetypes.clippingimage, ...).

This one keeps archetype's way of defining sizes and extends it to add an extra resize method parameter.

Migrating from Archetype's ImageField to CroppingImageField
===========================================================

Migrating existing ImageFields is as easy as switching from ImageField to CroppingImageField class.
If no resize method is specified, the default resize method of Archetype is used (scale).
Once switched to CroppingImageField you can add a third parameter to specify which resize method to use when generating each scale (see Sample schema definition)

Tests and examples
==================

Tests imports
-------------

Only used for testing
  >>> import os
  >>> from Products.Archetypes.tests.utils import mkDummyInContext
  >>> from Products.Archetypes.tests.utils import Dummy
  >>> from Products.Archetypes.atapi import *
  
This one must be imported in the type's module
  >>> from collective.croppingimagefield import fields as cif
	
Sample schema definition
------------------------
	
  >>> schema = BaseSchema + Schema((
  ...     cif.CroppingImageField('image',
  ...         original_size=    (800,600,
  ...                            cif.RESIZE_CROP),
  ...         sizes={'mini' :   (80,80), # default : scale (AT original behavior)
  ...                'normal' : (200,200,
  ...                            cif.RESIZE_SCALE),
  ...                'big' :    (300,300,
  ...                            cif.RESIZE_ZOOM),
  ...                'maxi' :   (500,500),
  ...                'header' : (500,150,
  ...                            cif.RESIZE_CROP)}),
  ... ))
	
Setting up testing datas
------------------------
	
Creating a dummy object using the schema
  >>> instance = mkDummyInContext(
  ...     Dummy, oid='dummy',
  ...     context=self.portal,
  ...     schema=schema)
  
Check that the image has been correctly loaded in the test case
  >>> self._image[:5]
  'GIF89'
  
Set the image and check that it has been stored in the image field
  >>> instance.setImage(self._image, mimetype='image/gif')
  >>> instance.getImage()
  <Image ...>

Image scales
------------

image is 800x600 (cropped so not 600x600)
  >>> instance.image.width, instance.image.height
  (800, 600)


There is an image_mini scale
  >>> instance.image_mini
  <Image ...>

It is 80x60 (Default (SCALE) : image is resized to fit in the rectangle) 
  >>> instance.image_mini.width, instance.image_mini.height
  (80, 60)


There is an image_normal scale
  >>> instance.image_normal
  <Image ...>

It is 200x150 (SCALE : image is resized to fit in the rectangle) 
  >>> instance.image_normal.width, instance.image_normal.height
  (200, 150)


There is an image_big scale
  >>> instance.image_big
  <Image ...>

It is 300x300 (SCALE : image is resized so the smallest side fit in the rectangle, and image overflow is kept) 
  >>> instance.image_big.width, instance.image_big.height
  (400, 300)


There is an image_header scale
  >>> instance.image_header
  <Image ...>

It is 500x150 (SCALE : image is resized so the smallest side fit in the rectangle, and image overflow is cropped) 
  >>> instance.image_header.width, instance.image_header.height
  (500, 150)
	