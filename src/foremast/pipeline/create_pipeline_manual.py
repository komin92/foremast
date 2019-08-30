#   Foremast - Pipeline Tooling
#
#   Copyright 2019 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Create manual Pipeline for Spinnaker."""
import json
import jinja2

from ..utils import get_pipeline_id, normalize_pipeline_name
from ..utils.lookups import FileLookup
from ..consts import TEMPLATES_PATH, TEMPLATES_SCHEME_IDENTIFIER
from .create_pipeline import SpinnakerPipeline
from .jinja_functions import JinjaFunctions

class SpinnakerPipelineManual(SpinnakerPipeline):
    """Manual JSON configured Spinnaker Pipelines."""

    def create_pipeline(self):
        """Use JSON files to create Pipelines."""
        pipelines = self.settings['pipeline']['pipeline_files']
        self.log.info('Uploading manual Pipelines: %s', pipelines)

        for i, file_name in enumerate(pipelines):

            json_string = self.get_pipeline_file_contents(file_name)

            # If this is a .j2 file render is template, otherwise treat as normal json file
            if file_name.endswith(".j2"):
                pipeline_vars = self.get_pipeline_variables_dict(i)
                json_string = self.get_rendered_json(json_string, pipeline_vars)

            pipeline_dict = json.loads(json_string)

            # Override template values that shoudl be set by foremast last
            pipeline_dict.setdefault('application', self.app_name)
            pipeline_dict.setdefault('name',
                                     normalize_pipeline_name(name=file_name.lstrip(TEMPLATES_SCHEME_IDENTIFIER)))
            pipeline_dict.setdefault('id', get_pipeline_id(app=pipeline_dict['application'],
                                                           name=pipeline_dict['name']))

            self.post_pipeline(pipeline_dict)

        return True

    def get_pipeline_file_contents(self, file_name):
        """Returns a string containing the file constants of the file passed in
        Supports local files, files in git and shared templates in the TEMPLATES_PATH"""
        # Check if this file is a shared template in the TEMPLATES_PATH
        if file_name.startswith(TEMPLATES_SCHEME_IDENTIFIER):
            file_name = file_name.lstrip(TEMPLATES_SCHEME_IDENTIFIER)
            pipeline_templates_path = TEMPLATES_PATH.rstrip("/") + "/pipeline"
            lookup = FileLookup(git_short=None, runway_dir=pipeline_templates_path)
            return lookup.get(filename=file_name)
        # Consider it a local repo file, check local or git:
        lookup = FileLookup(git_short=self.generated.gitlab()['main'], runway_dir=self.runway_dir)
        return lookup.get(filename=file_name)

    def get_rendered_json(self, json_string, pipeline_vars=None):
        """Takes a string of a manual template and renders it as a Jinja2 template, returning the result"""

        jinja_template = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(json_string)
        # Get any pipeline args defined in pipeline.json, default to empty dict if none defined
        pipeline_args = dict()

        # Expose permitted functions to jinja template
        jinja_functions = JinjaFunctions(self.app_name).get_dict()
        pipeline_args.update(jinja_functions)

        # If any args set in the pipeline file add them to the pipeline_args.variables
        if pipeline_vars is not None:
            pipeline_args["variables"] = pipeline_vars

        # Render the template
        return jinja_template.render(pipeline_args)

    def get_pipeline_variables_dict(self, index):
        """Safely gets the user defined variables from the pipeline.json file"""
        # Safely get variables out of pipeline.json if they are set
        pipe_settings = self.settings["pipeline"]
        if "pipeline_files_variables" in pipe_settings \
        and isinstance(pipe_settings['pipeline_files_variables'], list) \
        and len(pipe_settings['pipeline_files_variables']) > index:
            return pipe_settings['pipeline_files_variables'][index]

        # Default value is None
        return None
