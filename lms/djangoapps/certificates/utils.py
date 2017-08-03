"""Utilities to assist with certificates tasks."""
import logging
from urlparse import urljoin
from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from lxml import etree
import re

import cairosvg
from tempfile import NamedTemporaryFile
import os
import subprocess

from xmodule.contentstore.content import StaticContentStream, StaticContent
from xmodule.contentstore.django import contentstore
import base64
from xmodule.exceptions import NotFoundError

log = logging.getLogger(__name__)

def svg_filter_model(svgstringin):
    """
    This function is used both in the command helper and when generating mako template for the SVG model
    It places description field with mako scripts inside the related flowtext or textspan
    This way we can still edit the model with Inkscape and manage placeholder whilst using "fake" text to jugdge on the
    final result
    """
    xslstring = __get_xsl_string_model()

    return __get_append_to_model() + __basic_filter(svgstringin, xslstring)

def __basic_filter(svgstringin,xslstring):
    """
    This function is used both in the command helper and when generating mako template for the SVG model
    It places description field with mako scripts inside the related flowtext or textspan
    This way we can still edit the model with Inkscape and manage placeholder whilst using "fake" text to jugdge on the
    final result
    """
    strippedstring = re.sub(r'^\s*','' ,svgstringin).encode('utf-8')

    dom = etree.fromstring(strippedstring)
    xslt = etree.fromstring(xslstring)
    transform = etree.XSLT(xslt)
    newdom = transform(dom)

    return etree.tostring(newdom)

def svg_converter(svgstringin, content_type="image/png"):
    """
        This function callse Inkscape to convert to png or pdf. Cairosvg was not mature enough to enable nice styles or
        flowtext
        """
    convertedvalstring = ''
    convertedvalstring = __convert_via_inkscape(svgstringin, content_type)
    #convertedvalstring = cairosvg.surface.PDFSurface.convert(svgstringin)
    return convertedvalstring

def __convert_via_inkscape(stringin, content_type="image/png"):
    infile =  NamedTemporaryFile(delete=True)
    outfile = NamedTemporaryFile(delete=True)
    infile.write(stringin)
    infile.flush()
    exportarg = '--export-png='
    if content_type == "image/png":
        exportarg = '--export-png='
    elif content_type == "application/pdf":
        exportarg = '--export-pdf='
    subprocess.call(['inkscape', '-z','--export-background=#FFFFFF','--file=' + infile.name, exportarg + outfile.name])
    stringout = outfile.read()
    infile.close()
    outfile.close()
    return stringout


def __get_xsl_string_model():
    xslbody =  """
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:choose>
                <xsl:when test="./svg:desc">
                     <xsl:apply-templates select="@*|node()" mode='replacedesc'>
                          <xsl:with-param name="nodedesc" select="./svg:desc/text()"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:otherwise>
                            <xsl:apply-templates select="@*|node()"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:copy>
    </xsl:template>
    
    <xsl:template match="svg:g[@inkscape:label='#signatory']" mode="replacedesc">
        <xsl:text>&#10;</xsl:text><xsl:value-of select="./svg:desc/text()"/><xsl:text>&#10;</xsl:text>
        <xsl:copy>
            <xsl:apply-templates select="@*|node()">
            </xsl:apply-templates>
        </xsl:copy>
        <xsl:text>&#10;</xsl:text>% endif<xsl:text>&#10;</xsl:text>
    </xsl:template>

    <xsl:template match="svg:flowPara/text()" mode="replacedesc">
         <xsl:param name="nodedesc" />
         <xsl:value-of select="$nodedesc"/>
    </xsl:template>

    <xsl:template match="svg:image[@inkscape:label='#signatory-signature-image']">
      <xsl:copy>
            <xsl:attribute name='xlink:href'>
                <xsl:value-of select="./svg:desc/text()"/>
            </xsl:attribute>
            <xsl:apply-templates select="@*[not(name()='xlink:href')]"/>
     </xsl:copy>            
    </xsl:template>
    
    <xsl:template match="svg:desc" mode="replacedesc"/>
    
    <xsl:template match="@*|node()" mode="replacedesc">
        <xsl:param name="nodedesc" />
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" mode="replacedesc">
                <xsl:with-param name="nodedesc" select="$nodedesc"/>
            </xsl:apply-templates>
        </xsl:copy>
    </xsl:template>
    
    """
    return __get_xsl_string_basic(xslbody)

def __get_append_to_model():
    return """"""

def __get_xsl_string_basic(xslbody):
    return """<?xml version="1.0" encoding="UTF-8"?>
    <xsl:stylesheet version="1.0" 
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:cc="http://creativecommons.org/ns#"
        xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
        xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
        xmlns:svg="http://www.w3.org/2000/svg"
        xmlns="http://www.w3.org/2000/svg"
        xmlns:xlink="http://www.w3.org/1999/xlink" 
        >

    <xsl:output  omit-xml-declaration="yes" method="xml" indent="yes"/>
    """ + xslbody +  """
    </xsl:stylesheet>

    """

def get_svg_base64(imagepath):
    image_location = StaticContent.get_location_from_path(imagepath)  # calculate thumbnail 'location' in gridfs
    try:
        image_content = contentstore().find(image_location, as_stream=True)
        b64encoded = base64.b64encode(image_content.copy_to_in_mem().data)
        return "data:image/png;base64,"+b64encoded
    except NotFoundError:
        return ""
