"""Utility for converting a normal SVG into a templatable SVG file

Example usage:

    $ ./manage.py lms convert_svg_tomakotemplate -i originalfile.svg  -o destinationfile.svg

"""
import logging
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from lxml import etree

class Command(BaseCommand):
    """
    Management command to set or get the certificate whitelist
    for a given user(s)/course
    """

    help = """
    Converts a "normal" svg into a templatable SVG file

    """

    option_list = BaseCommand.option_list + (
        make_option('-i', '--infile',
                    metavar='INFILE',
                    dest='infile',
                    default=None,
                    help='File to read from and do the transformation from'),

        make_option('-o', '--outfile',
                    metavar='OUTFILE',
                    dest='outfile',
                    default=None,
                    help='File to write to (if this parameter is not present, out file will be <filename>.out'),

    )

    def handle(self, *args, **options):
        in_file = options['infile']
        if not in_file:
            raise CommandError("You must specify a source filename")

        out_file = options['outfile']

        dom = etree.parse(in_file)
        xslt = etree.fromstring(xslstring)
        transform = etree.XSLT(xslt)
        newdom = transform(dom)
        if not out_file:
            print newdom
        else:
            newdom.write(out_file)

xslstring = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:svg="http://www.w3.org/2000/svg" >

<xsl:output  omit-xml-declaration="yes" method="xml" indent="yes"/>

<xsl:template match="@*|node()">
    <xsl:copy>
        <xsl:choose>
            <xsl:when test="./svg:desc">
                <xsl:apply-templates select="node()" mode='replacedesc'>
                    <xsl:with-param name="nodedesc"><xsl:value-of select="//svg:desc/text()" /></xsl:with-param>
                </xsl:apply-templates>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="@*|node()"/>
        </xsl:otherwise>
        </xsl:choose>    
    </xsl:copy>
</xsl:template>

<xsl:template match="*" mode="replacedesc">
    <xsl:param name="nodedesc" />
    <xsl:copy>
     <xsl:apply-templates select="@*|node()" mode="replacedesc">
       <xsl:with-param name="nodedesc"><xsl:value-of select="$nodedesc"/></xsl:with-param>
     </xsl:apply-templates>
    </xsl:copy> 
</xsl:template>

<xsl:template match="svg:tspan/text()|svg:flowPara/text()" mode="replacedesc">
    <xsl:param name="nodedesc" />
    <xsl:value-of select="$nodedesc"/>
</xsl:template>

<xsl:template match="svg:desc" mode="replacedesc"/>


</xsl:stylesheet>

"""