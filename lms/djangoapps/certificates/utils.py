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

    <xsl:template match="//svg:flowPara/text()" mode="replacedesc">
         <xsl:param name="nodedesc" />
         <xsl:value-of select="$nodedesc"/>
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
    return """data:image/png;base64,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 UJFuKKz/Aw0+kfSguyAyAAAAAElFTkSuQmCC"""