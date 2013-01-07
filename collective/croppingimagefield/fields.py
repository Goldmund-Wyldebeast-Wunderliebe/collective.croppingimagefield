from cStringIO import StringIO

from Products.Archetypes.Field import HAS_PIL
from Products.Archetypes.Field import ImageField as AImageField

from Acquisition import aq_base
from plone.app.blob.config import blobScalesAttr

from Products.CMFPlone.utils import log, log_exc
from AccessControl import ClassSecurityInfo
from Products.CMFCore import permissions
from ZODB.POSException import ConflictError

from Products.CMFCore.permissions import View, ModifyPortalContent

from zope.interface import implements
from zope.component import adapts
from plone.app.blob.field import ImageField, BlobField
from plone.app.blob.utils import getImageSize, getPILResizeAlgo, openBlob
from plone.app.blob.scale import BlobImageScaleHandler, BlobImageScaleFactory
from plone.app.imaging.traverse import DefaultImageScaleHandler, ImageScale
from plone.app.blob.interfaces import IBlobImageField
from Products.Archetypes.Registry import registerField
from Products.Archetypes.atapi import ObjectField, FileWidget, ImageWidget
from zope.interface import Interface
from logging import exception
from ZODB.blob import Blob
from plone.app.imaging.interfaces import IImageScaleHandler, IImageScaling
from Products.Archetypes.interfaces import IImageField
from plone.app.blob.mixins import ImageFieldMixin


if HAS_PIL:
    import PIL

_marker = []

RESIZE_SCALE = 0
RESIZE_ZOOM = 1
RESIZE_CROP = 2
RESIZE_FILL_BLACK = 3
RESIZE_FILL_WHITE = 4
RESIZE_SCALE_MAX = 5

class BlobbyImageScaleHandler(object):
    
    implements(IImageScaleHandler)
    adapts(IImageField)
    
    
    def __init__(self, context):
        self.context = context
        
    def getScale(self, instance, scale, scaleType = 0):
        """ return scaled and aq-wrapped version for given image data """
        field = self.context
        available = field.getAvailableSizes(instance)
        if scale in available or scale is None:
            image = self.retrieveScale(instance, scale=scale)
            if not image:                
                if len(available[scale]) == 2:
                    width, height = available[scale]
                    scaleType = 0
                else:
                    width, height, scaleType = available[scale]
                data = self.createScale(instance, scale, width, height, scaleType = scaleType)
                if data is not None:
                    self.storeScale(instance, scale, **data)
                    image = self.retrieveScale(instance, scale=scale)
            if image is not None and not isinstance(image, basestring):
                return image
        return None
        
    def createScale(self, instance, scale, width, height, data=None, scaleType = 0):
        """ create & return a scaled version of the image as retrieved
            from the field or optionally given data """
        field = self.context
        if HAS_PIL and width and height:
            if data is None:
                image = field.getRaw(instance)
                if not image:
                    return None
                data = str(image.data)
            if data:
                id = field.getName() + '_' + scale
                try:
                    imgdata, format = field.resize(data, width, height, scaleType = scaleType)
                except (ConflictError, KeyboardInterrupt):
                    pass
                except Exception:
                    if not field.swallowResizeExceptions:
                        raise
                    else:
                        exception('could not scale ImageField "%s" of %s',
                            field.getName(), instance.absolute_url())
                        return None
                content_type = 'image/%s' % format.lower()
                filename = field.getFilename(instance)
                return dict(id=id, data=imgdata.getvalue(),
                    content_type=content_type, filename=filename)
        return None
        
    def retrieveScale(self, instance, scale):
        """ retrieve a scaled version of the image """
        field = self.context
        if scale is None:
            blob = field.getUnwrapped(instance)
            data = dict(id=field.getName(), blob=blob.getBlob(),
                content_type=blob.getContentType(),
                filename=blob.getFilename())
        else:
            fields = getattr(aq_base(instance), blobScalesAttr, {})
            scales = fields.get(field.getName(), {})
            data = scales.get(scale)
        if data is not None:
            blob = openBlob(data['blob'])
            # `updata_data` & friends (from `OFS`) should support file
            # objects, so we could use something like:
            #   ImageScale(..., data=blob.getIterator(), ...)
            # but it uses `len(data)`, so we'll stick with a string for now
            image = ImageScale(data['id'], data=blob.read(),
                content_type=data['content_type'], filename=data['filename'])
            blob.close()
            return image.__of__(instance)
        return None

    def storeScale(self, instance, scale, **data):
        """ store a scaled version of the image """
        field = self.context
        fields = getattr(aq_base(instance), blobScalesAttr, {})
        scales = fields.setdefault(field.getName(), {})
        data['blob'] = Blob()
        blob = data['blob'].open('w')
        blob.write(data['data'])
        blob.close()
        del data['data']
        scales[scale] = data
        setattr(instance, blobScalesAttr, fields)
        


class CroppingImageField(BlobField, ImageFieldMixin):
    """
    See README.txt for documentation and example
    """
    
    security = ClassSecurityInfo()
    
    _properties = BlobField._properties.copy()
    _properties.update({
        'type': 'image',
        'original_size': None,
        'max_size': None,
        'sizes': None,
        'swallowResizeExceptions': False,
        'pil_quality': 88,
        'pil_resize_algo': getPILResizeAlgo(),
        'default_content_type': 'image/png',
        'allowable_content_types': ('image/gif', 'image/jpeg', 'image/png'),
        'widget': ImageWidget,
    })

    def set(self, instance, value, **kwargs):
        super(CroppingImageField, self).set(instance, value, **kwargs)
        if hasattr(aq_base(instance), blobScalesAttr):
            delattr(aq_base(instance), blobScalesAttr)
    
    security.declareProtected(View, 'getScale')
    def getScale(self, instance, scale=None, **kwargs):
        """ get scale by name or original """
        if scale is None:
            return self.getUnwrapped(instance, **kwargs)
        handler = BlobbyImageScaleHandler(self)
        if handler is not None:
            return handler.getScale(instance, scale)
        return None
        
        
    def getHandler(self):
        return BlobbyImageScaleHandler(self)
        

    security.declarePrivate('resize')
    def resize(self, data, w, h, default_format = 'JPEG', scaleType = 0):
        """ resize image (with material from ImageTag_Hotfix)"""
        #make sure we have valid int's
        size = int(w), int(h)

        original_file=StringIO(data)
        image = PIL.Image.open(original_file)
        # consider image mode when scaling
        # source images can be mode '1','L,','P','RGB(A)'
        # convert to greyscale or RGBA before scaling
        # preserve palletted mode (but not pallette)
        # for palletted-only image formats, e.g. GIF
        # PNG compression is OK for RGBA thumbnails
        original_mode = image.mode
        if original_mode == '1':
            image = image.convert('L')
        elif original_mode == 'P':
            image = image.convert('RGBA')
        # ================= Begin mod ====================
        resize = int(scaleType)
        iw, ih = image.size
        dw, dh = size
        ir = float(iw) / float(ih)
        dr = float(dw) / float(dh)
        wr = float(dw) / float(iw)
        hr = float(dh) / float(ih)
        if resize == RESIZE_ZOOM:
            if ir > dr: # image larger than the desired size
                size = (int(iw*hr), dh)
            else:
                size = (dw, int(ih*wr))
            image=image.resize(size, self.pil_resize_algo)
        elif resize == RESIZE_CROP:
            l = t = 0
            if ir > dr: # image larger than the desired size
                osize = (int(iw*hr), dh)
                l = int((iw*hr - dw) / 2)
            else:
                osize = (dw, int(ih*wr))
                t = int((ih*wr - dh) / 2)
            image=image.resize(osize, self.pil_resize_algo)
            image=image.crop((l, t, l+dw, t+dh))
        elif resize == RESIZE_SCALE_MAX:
            if iw > dw or ih > dh: # image larger than the desired size
                size = (dw, int(ih*wr))
                image=image.resize(size, self.pil_resize_algo)
            #else do nothing to the image
        elif resize in [RESIZE_FILL_BLACK,RESIZE_FILL_WHITE,]:
            if ir > dr: # image larger than the desired size
                size = (dw, int(ih*wr))
            else:
                size = (int(iw*hr), dh)
            image=image.resize(size, self.pil_resize_algo)
            if resize == RESIZE_FILL_BLACK:
                image_background = PIL.Image.new('RGBA', (dw, dh), (0, 0, 0, 0) )
            else:
                image_background = PIL.Image.new('RGBA', (dw, dh), (255, 255, 255, 255) )
            sw, sh = size
            if sw<dw: # width of the new, scaled image lower than destination width
                box = (int((dw-sw)/2),0)
                if original_mode == 'RGBA':
                    image_background.paste(image, box, image)
                else:
                    image_background.paste(image, box)
            elif sh<dh: # height of the new, scaled image is lower than the destination height
                box = (0,int((dh-sh)/2))
                if original_mode == 'RGBA':
                    image_background.paste(image, box, image)
                else:
                    image_background.paste(image, box)
            else: # source and destination are of the same size
                image_background=image
            image=image_background
        else: # if resize == RESIZE_SCALE
            if ir > dr: # image larger than the desired size
                size = (dw, int(ih*wr))
            else:
                size = (int(iw*hr), dh)
            image=image.resize(size, self.pil_resize_algo)
            # ================= End mod ====================
        format = image.format and image.format or default_format
        # decided to only preserve palletted mode
        # for GIF, could also use image.format in ('GIF','PNG')
        if original_mode == 'P' and format == 'GIF':
            image = image.convert('P')
        thumbnail_file = StringIO()
        # quality parameter doesn't affect lossless formats
        image.save(thumbnail_file, format, quality=self.pil_quality)
        thumbnail_file.seek(0)
        return thumbnail_file, format.lower()


    security.declarePrivate('scale')
    scale = resize

registerField(CroppingImageField, title='Blob-aware CroppingImageField',
              description='Used for storing cropping image in blobs')