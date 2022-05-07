# -*-coding:utf-8-*-
"""
@FileName:
    main.py
@Description:
    entry point
@CreateTime:
    2021/10/08 18:48
"""
import os
import click
import yaml
from mnsim_noc.utils.registry import RegistryMeta
from mnsim_noc.Array import TimeSliceArray
from importlib import import_module
from MNSIM.Interface.utils.init_interface import _init_evaluation_interface
from MNSIM.Mapping_Model.Behavior_mapping import behavior_mapping
from MNSIM.Mapping_Model.Tile_connection_graph import TCG


def _init_component(cfg, registry_name, **addi_args):
    type_ = cfg[registry_name + "_type"]
    cfg = cfg.get(registry_name + "_cfg", None)
    if not cfg:
        cfg = {}
    # config items will override addi_args items
    addi_args.update(cfg)
    cls = RegistryMeta.get_class(registry_name, type_)
    return cls(**addi_args)


@click.group(help="MNSIM NoC")
def main():
    pass


# time slice run
@main.command(help="Time Slice")
@click.option("--quiet", "-q", is_flag=True, default=False, help='run without communication conflicts, default: False')
@click.option("--nn", "-NN", default='vgg8', help="NN model description (name), default: vgg8")
@click.option("-HWdes", "--hardware_description", default=os.path.join(os.getcwd(), "SimConfig.ini"),
              help="Hardware description file location & name, default:/MNSIM_NoC/SimConfig.ini")
@click.option("-Weights", "--weights", default=os.path.join(os.getcwd(), "cifar10_vgg8_params.pth"),
              help="NN model weights file location & name, default:/MNSIM_NoC/cifar10_vgg8_params.pth")
@click.option("-D", "--device", default=0,
              help="Determine hardware device for simulation, default: CPU")
@click.option("--time_slice_span", "-TSS", default=1, help='span of the timeslice in simulation (ns), default: 1')
@click.option("--inter_tile_bandwidth", "-ITB", default=20, help='inter_tile_bandwidth (Gbps), default: 20')
@click.option("--input_cache_size", "-ICS", default=64, help='input_cache_size (KB), default: 64')
@click.option("--output_cache_size", "-OCS", default=64, help='output_cache_size (KB), default: 64')
@click.option("--packet_size", "-PKS", default=10, help='packet size(B), default: 10')
@click.option("--no_communication_conflicts", "-NCC", is_flag=True, default=False)
@click.option("--allow_pipeline", "-AP", is_flag=True, default=False)
def time_slice(quiet, nn, hardware_description, weights, device, time_slice_span, inter_tile_bandwidth, input_cache_size, output_cache_size, packet_size, no_communication_conflicts, allow_pipeline):
    # init array
    # __TestInterface = TrainTestInterface(network_module=nn, dataset_module='MNSIM.Interface.cifar10', SimConfig_path=hardware_description, weights_file=weights, device=device)
    __TestInterface = _init_evaluation_interface(nn, "cifar10", hardware_description, None, device)
    structure_file = __TestInterface.get_structure()
    TCG_mapping = TCG(structure_file, hardware_description, False)
    # print('start NoC simulation')
    array = TimeSliceArray(TCG_mapping, time_slice_span, hardware_description, inter_tile_bandwidth, input_cache_size, output_cache_size, packet_size, no_communication_conflicts, allow_pipeline, quiet)
    # run the sim
    array.run()
