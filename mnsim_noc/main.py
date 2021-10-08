#-*-coding:utf-8-*-
"""
@FileName:
    main.py
@Description:
    entry point
@CreateTime:
    2021/10/08 18:48
"""
import click
import yaml
from mnsim_noc.utils.registry import RegistryMeta

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
@click.argument("cfg_file", required=True, type=str)
@click.option("--quiet", "-q", is_flag=True, default=False)
def time_slice(cfg_file, quiet):
    # load cfg
    with open(cfg_file, "r") as f:
        cfg = yaml.safe_load(f)
    # init array
    # TODO: ONLY FOR TEST
    array = _init_component(cfg, "array")
    array.run()