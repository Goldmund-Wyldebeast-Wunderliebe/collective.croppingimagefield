Introduction
============

Provides an image field that can crop, zoom or scale the image instead of just scaling it.
It is fully compatible with archetype's way of managing image sizes and cropped images can be accessed 
the traversal way ( context/image_[size_name]).

Use like:

    from collective.croppingimagefield import fields as cif
    

Instead of using ImageField(from plone.app.blob.field import ImageField), we now use (cif.CroppingImageField).
Within the sizes property, there is an extra field to specify the scaling type Plone should use for each scale. 
For instance:

    sizes= {
            'mini'  : (100,  100, cif.RESIZE_SCALE),
            'preview'  : (128,  128, cif.RESIZE_SCALE),
            'highlight'  : (100,  100, cif.RESIZE_CROP),
            'verhaal'  : (200,  150, cif.RESIZE_CROP),
            'zoeken'  : (256,  150, cif.RESIZE_CROP),
            'verwant' : (128, 96, cif.RESIZE_CROP),  
            'maps_popup' : (64, 96, cif.RESIZE_CROP),  

            'slideshow' : (516, 247, cif.RESIZE_CROP),  
    },

The available scaling methods are:

    cif.RESIZE_SCALE (regular Plone behaviour)
    cif.RESIZE_ZOOM (...)
    cif.RESIZE_CROP (Tries to fit the dimensions of the scale by cropping the image)
    cif.RESIZE_FILL_BLACK (Fills empty space with black)
    cif.RESIZE_FILL_WHITE (Fills empty space with white)
    cif.RESIZE_SCALE_MAX (...)
