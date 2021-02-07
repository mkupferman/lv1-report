#!/usr/bin/env python3

"""
This is a library to read Waves LV1 .emo session files
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import xlsxwriter

from .model import *

# Public classes


class Lv1Session:
    def __init__(self, lv1_session_file):
        self.lv1_session_file = lv1_session_file
        self._parseSessionFile()

    def _parseSessionFile(self):
        engine = create_engine('sqlite:///%s' % self.lv1_session_file)
        session = sessionmaker(bind=engine)
        self.session = session()

        # build rack slot lookup table
        self.device_rack = DeviceRack()
        for device in self.session.query(Device):
            self.device_rack.populate_rack(
                device.cluster_index, device.device_name.name)

        # build input name lookup table
        result = self.session.query(SnapshotChainer)
        result = result.filter(SnapshotChainer.snapshot_id == -1)
        result = result.join(Object)
        result = result.join(ClusterType)
        result = result.filter(ClusterType.name == 'Input')

        self.input_labels = {}
        for chainer in result:
            channel_number = chainer.rel_object.obj_index
            self.input_labels[channel_number] = chainer.name

        # build output name lookup table
        output_types = (
            'Group',
            'Aux',
            'Matrix',
            'Main',
            'Center',
            'Mono',
            'Cue',
            'Talkback')
        result = self.session.query(SnapshotChainer)
        result = result.filter(SnapshotChainer.snapshot_id == -1)
        result = result.join(Object)
        result = result.join(ClusterType)
        result = result.filter(ClusterType.name.in_(output_types))

        self.output_labels = {}
        for chainer in result:
            output_type = chainer.rel_object.rel_cluster_type.name
            output_type_enum = chainer.rel_object.obj_index
            output_label = chainer.name

            if output_type not in self.output_labels.keys():
                self.output_labels[output_type] = {}
            self.output_labels[output_type][output_type_enum] = output_label

        # build patching
        self.patches = PatchBay()

        results = self.session.query(Route).order_by(
            Route.dst_cluster_type).order_by(Route.dst_channel_index).order_by(
            Route.dst_channel_index)
        for result in results:
            destination_type = result.rel_dst_cluster_type.name
            source_type = result.rel_src_cluster_type.name

            if destination_type == 'Input':
                # channel input patch

                device_name = self.device_rack.get_name(
                    result.src_cluster_type_index)
                device_channel = result.src_channel_index
                channel_num = result.dst_cluster_type_index

                if result.dst_section_index == 1:
                    is_alternate = True
                else:
                    is_alternate = False

                # check if it's the "right" channel of a stereo input channel
                if result.dst_channel_index == 1:
                    input_channel = '%s-R' % "{:0>2d}".format(channel_num + 1)
                else:
                    input_channel = "{:0>2d}".format(channel_num + 1)

                # see if other channel (L/R) of this input already patched
                existing_input = self.patches.get_patchbay_by_dst_index(
                    input_channel)
                if existing_input is None:
                    patch_item = RoutingPatch(
                        device_name,
                        device_channel + 1,
                        'Input',
                        input_channel,
                        is_alternate)
                    if channel_num in self.input_labels.keys():
                        patch_item.set_dst_label(
                            self.input_labels[channel_num])
                    self.patches.add_input(patch_item)
                else:
                    existing_input.set_src(
                        device_name, device_channel + 1, is_alternate)

            elif source_type == 'Inputs' and destination_type == 'Outputs':
                # device-to-device patch

                source_device_name = self.device_rack.get_name(
                    result.src_cluster_type_index)
                source_device_channel = result.src_channel_index
                destination_device_name = self.device_rack.get_name(
                    result.dst_cluster_type_index)
                destination_device_channel = result.dst_channel_index

                patch_item = RoutingPatch(
                    source_device_name,
                    source_device_channel + 1,
                    destination_device_name,
                    destination_device_channel + 1)
                self.patches.add_devicedevice(patch_item)

            elif destination_type == 'Outputs':
                # output patch

                destination_device_name = self.device_rack.get_name(
                    result.dst_cluster_type_index)
                destination_device_channel = result.dst_channel_index
                source_type_enum = result.src_cluster_type_index  # e.g. Matrix "0"

                # check if it's the "right" channel of a stereo source
                if result.src_channel_index == 1:
                    src_index = '%s-R' % str(source_type_enum + 1)
                else:
                    src_index = source_type_enum + 1

                patch_item = RoutingPatch(
                    source_type,
                    src_index,
                    destination_device_name,
                    destination_device_channel + 1)
                if source_type in self.output_labels.keys(
                ) and source_type_enum in self.output_labels[source_type]:
                    patch_item.set_src_label(
                        self.output_labels[source_type][source_type_enum])

                self.patches.add_output(patch_item)


class Lv1ExcelExporter:
    def __init__(self, lv1_session):
        self.lv1_session = lv1_session

    def writeFile(self, report_path):
        workbook = xlsxwriter.Workbook(report_path)

        heading = workbook.add_format({'bold': True, 'align': 'center'})
        cell = workbook.add_format({'align': 'left'})
        cell_bold = workbook.add_format({'bold': True, 'align': 'left'})

        # inputs
        ws_input = workbook.add_worksheet('Input')

        ws_input.write(0, 0, 'Channel', heading)
        ws_input.set_column('A:A', 15)
        ws_input.write(0, 1, 'Source Device [A]', heading)
        ws_input.set_column('B:B', 20)
        ws_input.write(0, 2, 'Source Ch. [A]', heading)
        ws_input.set_column('C:C', 15)
        ws_input.write(0, 3, 'Source Device [B]', heading)
        ws_input.set_column('D:D', 20)
        ws_input.write(0, 4, 'Source Ch. [B]', heading)
        ws_input.set_column('E:E', 15)

        row = 1

        for input in self.lv1_session.patches.get_inputs():
            if input.dst_label is None:
                channel_label = input.dst_index
            else:
                channel_label = '%s (%s)' % (input.dst_index, input.dst_label)

            ws_input.write(row, 0, channel_label, cell_bold)

            if input.has_primary():
                ws_input.write(row, 1, input.src_name, cell)
                ws_input.write(row, 2, input.src_index, cell)
            if input.has_alternate():
                ws_input.write(row, 3, input.src_name_alt, cell)
                ws_input.write(row, 4, input.src_index_alt, cell)

            row = row + 1

        # outputs
        ws_output = workbook.add_worksheet('Output')

        ws_output.write(0, 0, 'Destination', heading)
        ws_output.set_column('A:A', 20)
        ws_output.write(0, 1, 'Dest. Ch.', heading)
        ws_output.set_column('B:B', 10)
        ws_output.write(0, 2, 'Signal Source', heading)
        ws_output.set_column('C:C', 15)
        ws_output.write(0, 3, 'Source Label', heading)
        ws_output.set_column('D:D', 15)

        row = 1
        for output in self.lv1_session.patches.get_outputs():
            ws_output.write(row, 0, output.dst_name, cell)
            ws_output.write(row, 1, output.dst_index, cell)
            ws_output.write(row, 2, "%s %s" %
                            (output.src_name, output.src_index), cell)

            if output.src_label is not None:
                ws_output.write(row, 3, output.src_label, cell)

            row = row + 1

        # device-to-device
        ws_devicedevice = workbook.add_worksheet('Dev-to-Dev')

        ws_devicedevice.write(0, 0, 'Source Device', heading)
        ws_devicedevice.set_column('A:A', 20)
        ws_devicedevice.write(0, 1, 'Source. Ch.', heading)
        ws_devicedevice.set_column('B:B', 10)
        ws_devicedevice.write(0, 2, 'Dest. Device', heading)
        ws_devicedevice.set_column('C:C', 20)
        ws_devicedevice.write(0, 3, 'Dest. Ch.', heading)
        ws_devicedevice.set_column('D:D', 10)

        row = 1
        for devicedevice in self.lv1_session.patches.get_devicedevice():
            ws_devicedevice.write(row, 0, devicedevice.src_name, cell)
            ws_devicedevice.write(row, 1, devicedevice.src_index, cell)
            ws_devicedevice.write(row, 2, devicedevice.dst_name, cell)
            ws_devicedevice.write(row, 3, devicedevice.dst_index, cell)
            row = row + 1

        workbook.close()

# Private classes


class DeviceRack:
    """ uses 0-enumerated numbering internally """

    def __init__(self):
        self.names = {}

    def populate_rack(self, slot, name):
        self.names[slot] = name

    def get_name(self, slot):
        if slot in self.names:
            return self.names[slot]
        else:
            return 'EmptySlot%s' % str(slot + 1)


class RoutingPatch:
    """ uses 1-enumerated numbering -- for display """

    def __init__(
            self,
            src_name,
            src_index,
            dst_name,
            dst_index,
            is_alternate=False):
        self.dst_name = dst_name
        self.dst_index = dst_index
        self.src_label = None
        self.dst_label = None
        self.src_name = None
        self.src_index = None
        self.src_name_alt = None
        self.src_index_alt = None

        self.set_src(src_name, src_index, is_alternate)

    def set_src(self, src_name, src_index, is_alternate=False):
        if is_alternate:  # 'B' input
            self.src_name_alt = src_name
            self.src_index_alt = src_index
        else:
            self.src_name = src_name
            self.src_index = src_index

    def set_src_label(self, src_label):
        if len(src_label) > 0:
            self.src_label = src_label

    def set_dst_label(self, dst_label):
        if len(dst_label) > 0:
            self.dst_label = dst_label

    def has_alternate(self):
        return self.src_index_alt is not None

    def has_primary(self):
        return self.src_index is not None

    def __repr__(self):
        return "<RoutingPatch( %s[%s] --> %s[%s] )>" % (self.src_name,
                                                        self.src_index, self.dst_name, self.dst_index)


class PatchBay:
    def __init__(self):
        self.inputs = []
        self.outputs = []
        self.devicedevice = []

    def add_input(self, patch_item):
        self.inputs.append(patch_item)

    def get_inputs(self):
        self.inputs = sorted(self.inputs, key=lambda x: (x.dst_index))
        return self.inputs

    def add_devicedevice(self, patch_item):
        self.devicedevice.append(patch_item)

    def get_devicedevice(self):
        self.devicedevice = sorted(
            self.devicedevice,
            key=lambda x: (
                x.src_name,
                x.src_index,
                x.dst_name,
                x.dst_index))
        return self.devicedevice

    def get_patchbay_by_dst_index(self, dst_index):
        for input in self.inputs:
            if input.dst_index == dst_index:
                return input
        return None

    def add_output(self, patch_item):
        self.outputs.append(patch_item)

    def get_outputs(self):
        self.outputs = sorted(
            self.outputs,
            key=lambda x: (
                x.dst_name,
                x.dst_index,
                x.src_name,
                x.src_index))
        return self.outputs
