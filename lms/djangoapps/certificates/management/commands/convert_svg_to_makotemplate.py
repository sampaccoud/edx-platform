"""Utility for converting a normal SVG into a templatable SVG file

Example usage:

    $ ./manage.py lms convert_svg_tomakotemplate -i originalfile.svg  -o destinationfile.svg

"""
import logging
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import codecs

from certificates.utils import svg_filter_model

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

        with codecs.open(in_file,'r','utf-8') as fin:
            fstring = fin.read()
            svgout = svg_filter_model(fstring);
            if not out_file:
                print svgout
            else:
                with open(out_file) as fout:
                    fout.write(svgout)
