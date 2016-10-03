import json
import jsonschema

from functools import partial
from unittest.mock import mock_open, patch, PropertyMock
from unittest import TestCase
from qcodes.config import Config

VALID_JSON = "{}"
ENV_KEY = "/dev/random"
BAD_JSON = "{}"

# example configs
GOOD_CONFIG_MAP = {Config.default_file_name: {"z": 1, "a": 1, "b": 0},
                   ENV_KEY: {"z": 3, "h": 2, "user": {"foo":  "1"}},
                   Config.home_file_name: {"z": 3, "b": 2},
                   Config.cwd_file_name: {"z": 4, "c": 3, "bar": True}}

# in this case the home config is messging up a type
BAD_CONFIG_MAP = {Config.default_file_name: {"z": 1, "a": 1, "b": 0},
                  ENV_KEY: {"z": 3, "h": 2, "user": {"foo":  1}},
                  Config.home_file_name: {"z": 3, "b": "2", "user": "foo"},
                  Config.cwd_file_name: {"z": 4, "c": 3, "bar": True}}

# expected config after successful loading of config files
CONFIG = {"a": 1, "b": 2, "h": 2,
          "user": {"foo":  "1"},
          "c": 3, "bar": True, "z": 4}

# expected config after updade by user
UPDATED_CONFIG = {"a": 1, "b": 2, "h": 2,
                  "user": {"foo":  "bar"},
                  "c": 3, "bar": True, "z": 4}

# the schema does not cover extra fields, so users can pass
# wathever they want
SCHEMA = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "a": {
                "type": "integer"
                },
            "b": {
                "type": "integer"
                },
            "z": {
                "type": "integer"
                },
            "c": {
                "type": "integer"
                },
            "bar": {
                "type": "boolean"
                },
            "user": {
                "type": "object",
                "properties": {}
                }
            },
        "required": [
            "z"
            ]
        }

USER_SCHEMA = """ {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                           "foo":
                           {
                               "type": "string",
                               "description": "foo"
                               }
                           }
                       }
                   }
               }
        } """


def side_effect(map, name):
    return map[name]


class TestConfig(TestCase):
    def setUp(self):
        self.conf = Config()

    def test_missing_config_file(self):
        with self.assertRaises(FileNotFoundError):
            self.conf.load_config("./missing.json")

    @patch.object(Config, 'schema', new_callable=PropertyMock)
    @patch.object(Config, 'env_file_name', new_callable=PropertyMock)
    @patch.object(Config, 'load_config')
    @patch('os.path.isfile')
    def test_default_config_files(self, isfile, load_config, env, schema):
        # don't try to load custom schemas
        self.conf.schema_cwd_file_name = None
        self.conf.schema_home_file_name = None
        self.conf.schema_env_file_name = None
        schema.return_value = SCHEMA
        env.return_value = ENV_KEY
        isfile.return_value = True
        load_config.side_effect = partial(side_effect, GOOD_CONFIG_MAP)
        config = self.conf.load_default()
        self.assertEqual(config, CONFIG)

    @patch.object(Config, 'schema', new_callable=PropertyMock)
    @patch.object(Config, 'env_file_name', new_callable=PropertyMock)
    @patch.object(Config, 'load_config')
    @patch('os.path.isfile')
    def test_bad_config_files(self, isfile, load_config, env, schema):
        # don't try to load custom schemas
        self.conf.schema_cwd_file_name = None
        self.conf.schema_home_file_name = None
        self.conf.schema_env_file_name = None
        schema.return_value = SCHEMA
        env.return_value = ENV_KEY
        isfile.return_value = True
        load_config.side_effect = partial(side_effect, BAD_CONFIG_MAP)
        with self.assertRaises(jsonschema.exceptions.ValidationError):
                self.conf.load_default()

    @patch.object(Config, 'schema', new_callable=PropertyMock)
    @patch.object(Config, 'env_file_name', new_callable=PropertyMock)
    @patch.object(Config, 'load_config')
    @patch('os.path.isfile')
    @patch("builtins.open", mock_open(read_data=USER_SCHEMA))
    def test_user_schema(self, isfile, load_config, env, schema):
        schema.return_value = copy.deepcopy(SCHEMA)
        env.return_value = ENV_KEY
        isfile.return_value = True
        load_config.side_effect = partial(side_effect, GOOD_CONFIG_MAP)
        config = self.conf.load_default()
        self.assertEqual(config, CONFIG)

    @patch.object(Config, 'schema', new_callable=PropertyMock)
    @patch.object(Config, 'env_file_name', new_callable=PropertyMock)
    @patch.object(Config, 'load_config')
    @patch('os.path.isfile')
    @patch("builtins.open", mock_open(read_data=USER_SCHEMA))
    def test_bad_user_schema(self, isfile, load_config, env, schema):
        schema.return_value = copy.deepcopy(SCHEMA)
        env.return_value = ENV_KEY
        isfile.return_value = True
        load_config.side_effect = partial(side_effect, BAD_CONFIG_MAP)
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            self.conf.load_default()

