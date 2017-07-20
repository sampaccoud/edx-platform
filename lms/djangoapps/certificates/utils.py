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

def svg_filter(svgstringin):
    xslstring = __get_xsl_tring()

    strippedstring = re.sub(r'^\s*','' ,svgstringin).encode('utf-8')

    dom = etree.fromstring(strippedstring)
    xslt = etree.fromstring(xslstring)
    transform = etree.XSLT(xslt)
    newdom = transform(dom)

    return etree.tostring(newdom)

def __get_xsl_tring():
    return """<?xml version="1.0" encoding="UTF-8"?>
    <xsl:stylesheet version="2.0" 
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:cc="http://creativecommons.org/ns#"
        xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
        xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
        xmlns:svg="http://www.w3.org/2000/svg"
        xmlns="http://www.w3.org/2000/svg"
        >

    <xsl:output  omit-xml-declaration="yes" method="xml" indent="yes"/>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:choose>
                <xsl:when test="./svg:desc">
                     <xsl:apply-templates mode='replacedesc'>
                          <xsl:with-param name="nodedesc" select="./svg:desc/text()"/>
                    </xsl:apply-templates>
                </xsl:when>
                     <xsl:otherwise>
                            <xsl:apply-templates select="@*|node()"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:copy>
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




    </xsl:stylesheet>

    """

def svg_converter(svgstringin, content_type="image/png"):
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