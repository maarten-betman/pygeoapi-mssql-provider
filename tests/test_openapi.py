import yaml
from pygeoapi.util import (filter_dict_by_key_value, get_provider_by_type,
                           filter_providers_by_type, to_json, yaml_load)

from pygeoapi.openapi import generate_openapi_document, get_oas

def test_openapi():
    with open("../boka.config.yml") as ff:
        s = yaml_load(ff)
        pretty_print = s['server'].get('pretty_print', False)

        yaml.safe_dump(get_oas(s), default_flow_style=False)

        to_json(get_oas(s), pretty=pretty_print)
