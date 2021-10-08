#-*-coding:utf-8-*-
"""
@FileName:
    registry.py
@Description:
    RegistryMeta
@CreateTime:
    2021/10/08 17:32
"""
import abc
import collections

from mnsim_noc.utils.log import getLogger

__all__ = ["RegistryMeta", "RegistryError"]

class RegistryError(Exception):
    pass

LOGGER = getLogger("registry")
class RegistryMeta(abc.ABCMeta):
    registry_dict = collections.defaultdict(dict)

    def __init__(cls, name, bases, namespace):
        super(RegistryMeta, cls).__init__(name, bases, namespace)
        # base class should have REGISTRY
        if hasattr(cls, "REGISTRY"):
            # register the class
            table = cls.REGISTRY
            abstract_methods = cls.__abstractmethods__
            # leaf class should have no abstract methods
            if not abstract_methods:
                entry = namespace.get("NAME", name.lower())
                setattr(cls, "NAME", entry)
                RegistryMeta.registry_dct[table][entry] = cls
                LOGGER.debug(
                    "Register class {} as entry {} in table {}.".format(
                        name, entry, table
                    )
                )
            else:
                # non leaf classes should have no name
                if "NAME" in namespace:
                    entry = namespace["NAME"]
                    LOGGER.warning(
                        "Can't register abstract class {} as entry {} in table {}, ignore. Abstract methods: {}".format(
                            name, entry, table, ", ".join(abstract_methods)
                        )
                    )

    @classmethod
    def get_class(mcs, table, name):
        try:
            print(mcs.registry_dict)
            return mcs.all_classes(table)[name]
        except KeyError:
            raise RegistryError(
                "No registry item {} available in registry {}.".format(
                    name, table
                )
            )

    @classmethod
    def all_classes(mcs, table):
        try:
            return mcs.registry_dict[table]
        except KeyError:
            raise RegistryError("No registry table {} available.".format(table))

    @classmethod
    def avail_tables(mcs):
        return mcs.registry_dict.keys()

    def all_classes_(cls):
        return RegistryMeta.all_classes(cls.REGISTRY)

    def get_class_(cls, name):
        return RegistryMeta.get_class(cls.REGISTRY, name)
