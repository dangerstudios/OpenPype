# -*- coding: utf-8 -*-
# flake8: noqa E402
"""Pype module API."""
# add vendor to sys path based on Python version
import sys
import os
import site

# Add Python version specific vendor folder
python_version_dir = os.path.join(
    os.getenv("OPENPYPE_REPOS_ROOT", ""),
    "openpype", "vendor", "python", "python_{}".format(sys.version[0])
)
# Prepend path in sys paths
sys.path.insert(0, python_version_dir)
site.addsitedir(python_version_dir)


from .env_tools import (
    env_value_to_bool,
    get_paths_from_environ,
    get_global_environments
)

from .terminal import Terminal
from .execute import (
    get_pype_execute_args,
    execute,
    run_subprocess
)
from .log import PypeLogger, timeit
from .mongo import (
    decompose_url,
    compose_url,
    get_default_components,
    validate_mongo_connection,
    OpenPypeMongoConnection
)
from .anatomy import (
    merge_dict,
    Anatomy
)

from .config import get_datetime_data

from .vendor_bin_utils import (
    get_vendor_bin_path,
    get_oiio_tools_path,
    get_ffmpeg_tool_path,
    ffprobe_streams
)

from .python_module_tools import (
    modules_from_path,
    recursive_bases_from_class,
    classes_from_module
)

from .avalon_context import (
    is_latest,
    any_outdated,
    get_asset,
    get_hierarchy,
    get_linked_assets,
    get_latest_version,

    get_workdir_data,
    get_workdir,
    get_workdir_with_workdir_data,

    create_workfile_doc,
    save_workfile_data_to_doc,
    get_workfile_doc,

    BuildWorkfile,

    get_creator_by_name,

    change_timer_to_current_context
)

from .local_settings import (
    IniSettingRegistry,
    JSONSettingRegistry,
    OpenPypeSecureRegistry,
    OpenPypeSettingsRegistry,
    get_local_site_id,
    change_openpype_mongo_url,
    get_openpype_username
)

from .applications import (
    ApplicationLaunchFailed,
    ApplictionExecutableNotFound,
    ApplicationNotFound,
    ApplicationManager,

    PreLaunchHook,
    PostLaunchHook,

    EnvironmentPrepData,
    prepare_host_environments,
    prepare_context_environments,
    get_app_environments_for_context,
    apply_project_environments_value,

    compile_list_of_regexes
)

from .profiles_filtering import filter_profiles

from .plugin_tools import (
    TaskNotSetError,
    get_subset_name,
    filter_pyblish_plugins,
    source_hash,
    get_unique_layer_name,
    get_background_layers,
    oiio_supported,
    decompress,
    get_decompress_dir,
    should_decompress
)

from .path_tools import (
    version_up,
    get_version_from_path,
    get_last_version_from_path
)

from .editorial import (
    is_overlapping_otio_ranges,
    otio_range_to_frame_range,
    otio_range_with_handles,
    convert_to_padded_path,
    trim_media_range,
    range_from_frames,
    frames_to_secons,
    make_sequence_collection
)

terminal = Terminal

__all__ = [
    "get_pype_execute_args",
    "execute",
    "run_subprocess",

    "env_value_to_bool",
    "get_paths_from_environ",
    "get_global_environments",

    "get_vendor_bin_path",
    "get_oiio_tools_path",
    "get_ffmpeg_tool_path",
    "ffprobe_streams",

    "modules_from_path",
    "recursive_bases_from_class",
    "classes_from_module",

    "is_latest",
    "any_outdated",
    "get_asset",
    "get_hierarchy",
    "get_linked_assets",
    "get_latest_version",

    "get_workdir_data",
    "get_workdir",
    "get_workdir_with_workdir_data",

    "create_workfile_doc",
    "save_workfile_data_to_doc",
    "get_workfile_doc",

    "BuildWorkfile",

    "get_creator_by_name",

    "change_timer_to_current_context",

    "IniSettingRegistry",
    "JSONSettingRegistry",
    "OpenPypeSecureRegistry",
    "OpenPypeSettingsRegistry",
    "get_local_site_id",
    "change_openpype_mongo_url",
    "get_openpype_username",

    "ApplicationLaunchFailed",
    "ApplictionExecutableNotFound",
    "ApplicationNotFound",
    "ApplicationManager",
    "PreLaunchHook",
    "PostLaunchHook",
    "EnvironmentPrepData",
    "prepare_host_environments",
    "prepare_context_environments",
    "get_app_environments_for_context",
    "apply_project_environments_value",

    "compile_list_of_regexes",

    "filter_profiles",

    "TaskNotSetError",
    "get_subset_name",
    "filter_pyblish_plugins",
    "source_hash",
    "get_unique_layer_name",
    "get_background_layers",
    "oiio_supported",
    "decompress",
    "get_decompress_dir",
    "should_decompress",

    "version_up",
    "get_version_from_path",
    "get_last_version_from_path",

    "terminal",

    "merge_dict",
    "Anatomy",

    "get_datetime_data",

    "PypeLogger",
    "decompose_url",
    "compose_url",
    "get_default_components",
    "validate_mongo_connection",
    "OpenPypeMongoConnection",

    "timeit",

    "is_overlapping_otio_ranges",
    "otio_range_with_handles",
    "convert_to_padded_path",
    "otio_range_to_frame_range",
    "trim_media_range",
    "range_from_frames",
    "frames_to_secons",
    "make_sequence_collection"
]
