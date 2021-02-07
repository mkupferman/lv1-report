#!/usr/bin/env python3

"""
.emo sqlite3 file models
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class SrcRoutingType(Base):
    __tablename__ = 'src_routing_type'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Text)

    def __repr__(self):
        return "<SrcRoutingType(name='%s')>" % self.name


class DstRoutingType(Base):
    __tablename__ = 'dst_routing_type'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Text)

    def __repr__(self):
        return "<DstRoutingType(name='%s')>" % self.name


class ClusterType(Base):
    __tablename__ = 'cluster_type'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Text)

    def __repr__(self):
        return "<ClusterType(name='%s')>" % self.name


class Object(Base):
    __tablename__ = 'object'
    id = Column(Integer, primary_key=True, nullable=False)
    obj_type = Column(Integer, ForeignKey('cluster_type.id'))
    obj_index = Column(Integer, nullable=False)

    rel_cluster_type = relationship("ClusterType")

    def __repr__(self):
        return "<Object(id='%s')>" % self.id


class SnapshotChainer(Base):
    __tablename__ = 'snapshot_chainer'
    id = Column(Integer, primary_key=True, nullable=False)
    snapshot_id = Column(Integer, nullable=False)
    name = Column(Text)
    chainer_id = Column(Integer, ForeignKey('object.id'))

    rel_object = relationship("Object")

    def __repr__(self):
        return "<SnapshotChainer(id='%s', name='%s')>" % (self.id, self.name)


class DeviceName(Base):
    __tablename__ = 'device_name'
    # not technically a PK...
    mac = Column(BigInteger, primary_key=True, nullable=False)
    name = Column(Text)

    def __repr__(self):
        return "<DeviceName(name='%s')>" % self.name


class Device(Base):
    __tablename__ = 'device'
    id = Column(Integer, primary_key=True, nullable=False)
    io_bank = Column(Integer, nullable=False)
    assign = Column(Integer)
    mac = Column(BigInteger, ForeignKey('device_name.mac'))

    device_name = relationship("DeviceName")

    @hybrid_property
    def cluster_index(self):
        return self.io_bank * 8 + self.assign

    def __repr__(self):
        return "<Device(mac='%s')>" % self.mac


class Route(Base):
    __tablename__ = 'routes'
    id = Column(Integer, primary_key=True, nullable=False)
    src_cluster_type = Column(Integer, ForeignKey('cluster_type.id'))
    src_cluster_type_index = Column(
        Integer, ForeignKey('device.cluster_index'))
    # output's stereo channel OR dev-to-dev's source channel #
    src_channel_index = Column(Integer, nullable=False)
    dst_cluster_type = Column(Integer, ForeignKey('cluster_type.id'))
    dst_cluster_type_index = Column(Integer, nullable=False)
    # input's L/R OR chan # for output/d2d
    dst_channel_index = Column(Integer, nullable=False)
    dst_section_index = Column(Integer, nullable=False)  # 'A' or 'B' input
    #status = Column(Integer, nullable=False)

    rel_src_cluster_type = relationship(
        "ClusterType", primaryjoin="Route.src_cluster_type==ClusterType.id")
    rel_dst_cluster_type = relationship(
        "ClusterType", primaryjoin="Route.dst_cluster_type==ClusterType.id")

    def __repr__(self):
        return "<Route(id='%s')" % self.id
