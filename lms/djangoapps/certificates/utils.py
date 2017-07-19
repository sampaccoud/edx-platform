"""Utilities to assist with certificates tasks."""
import logging
from urlparse import urljoin
from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from lxml import etree
import re

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


    # <xsl:template match="@*|node()">
    #     <xsl:copy>
    #         <xsl:choose>
    #             <xsl:when test="./svg:desc">
    #                 <xsl:apply-templates select="node()" mode='replacedesc'>
    #                     <xsl:with-param name="nodedesc"><xsl:value-of select="//svg:desc/text()" /></xsl:with-param>
    #                 </xsl:apply-templates>
    #             </xsl:when>
    #             <xsl:otherwise>
    #                 <xsl:apply-templates select="@*|node()"/>
    #         </xsl:otherwise>
    #         </xsl:choose>
    #     </xsl:copy>
    # </xsl:template>
    #    <xsl:value-of select=".//svg:desc/text()" />