""" Dit is een plugin ! 

    Hoera, hoera, hoera
"""
from argparse import ArgumentParser, Namespace
from plugins.plugin import PluginBase
from process.aapa_processor.aapa_processor import AAPARunnerContext


class TestPlugin3(PluginBase):
    def get_parser(self)->ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--migrate', dest='migrate', type=str,help='create SQL output from e.g. detect or student in this directory') 
        parser.add_argument('-v', '--verbose', action="store_true", help='If true: logging gaat naar de console ipv het logbestand.')
        return parser

    def process(self, context: AAPARunnerContext, **kwdargs):        
        print(f'Process all: test3 {self.aapa_dict}')
        print(f'args are {kwdargs}')
        print(context.configuration.config_options)
        return True
