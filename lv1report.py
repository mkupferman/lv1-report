#!/usr/bin/env python3

import os
import sys
import time
import click
from pathlib import Path, PurePath
from pylv1emo import Lv1Session, Lv1ExcelExporter


@click.command()
@click.argument('session-file', type=click.Path(exists=True))
@click.option('--report-file', '-f', default=None, type=click.Path(),
              help='Specify report file path, otherwise one will be generated in the same directory as the session file.')
def lv1report(session_file, report_file):
    session_path = Path(session_file)
    session_ppath = PurePath(session_path)

    if report_file is None:
        session_directory = session_ppath.parent
        session_filename = session_ppath.name
        session_stem = session_ppath.stem
        report_filename = '%s-%s.xlsx' % (session_stem,
                                          time.strftime('%Y%m%dT%H%M%S'))
        report_path = Path(session_directory / report_filename)
    else:
        report_path = Path(report_file)

    print("Reading session %s" % session_path, file=sys.stderr)
    session = Lv1Session(session_path)

    print("Writing report to %s" % report_path, file=sys.stderr)
    report = Lv1ExcelExporter(session)
    report.writeFile(report_path)
