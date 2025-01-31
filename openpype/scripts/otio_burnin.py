import os
import sys
import re
import subprocess
import platform
import json
import opentimelineio_contrib.adapters.ffmpeg_burnins as ffmpeg_burnins
from openpype.api import resources
import openpype.lib


ffmpeg_path = openpype.lib.get_ffmpeg_tool_path("ffmpeg")
ffprobe_path = openpype.lib.get_ffmpeg_tool_path("ffprobe")


FFMPEG = (
    '"{}" -i "%(input)s" %(filters)s %(args)s%(output)s'
).format(ffmpeg_path)

FFPROBE = (
    '"{}" -v quiet -print_format json -show_format -show_streams "%(source)s"'
).format(ffprobe_path)

DRAWTEXT = (
    "drawtext=fontfile='%(font)s':text=\\'%(text)s\\':"
    "x=%(x)s:y=%(y)s:fontcolor=%(color)s@%(opacity).1f:fontsize=%(size)d"
)
TIMECODE = (
    "drawtext=timecode=\\'%(timecode)s\\':text=\\'%(text)s\\'"
    ":timecode_rate=%(fps).2f:x=%(x)s:y=%(y)s:fontcolor="
    "%(color)s@%(opacity).1f:fontsize=%(size)d:fontfile='%(font)s'"
)

MISSING_KEY_VALUE = "N/A"
CURRENT_FRAME_KEY = "{current_frame}"
CURRENT_FRAME_SPLITTER = "_-_CURRENT_FRAME_-_"
TIMECODE_KEY = "{timecode}"
SOURCE_TIMECODE_KEY = "{source_timecode}"


def _streams(source):
    """Reimplemented from otio burnins to be able use full path to ffprobe
    :param str source: source media file
    :rtype: [{}, ...]
    """
    command = FFPROBE % {'source': source}
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out = proc.communicate()[0]
    if proc.returncode != 0:
        raise RuntimeError("Failed to run: %s" % command)
    return json.loads(out)['streams']


def get_fps(str_value):
    if str_value == "0/0":
        print("WARNING: Source has \"r_frame_rate\" value set to \"0/0\".")
        return "Unknown"

    items = str_value.split("/")
    if len(items) == 1:
        fps = float(items[0])

    elif len(items) == 2:
        fps = float(items[0]) / float(items[1])

    # Check if fps is integer or float number
    if int(fps) == fps:
        fps = int(fps)

    return str(fps)


class ModifiedBurnins(ffmpeg_burnins.Burnins):
    '''
    This is modification of OTIO FFmpeg Burnin adapter.
    - requires FFmpeg in PATH

    Offers 6 positions for burnin text. Each can be set with:
    - static text
    - frames
    - timecode

    Options - dictionary which sets the final look.
    - Datatypes explanation:
    <color> string format must be supported by FFmpeg.
        Examples: "#000000", "0x000000", "black"
    <font> must be accesible by ffmpeg = name of registered Font in system or path to font file.
        Examples: "Arial", "C:/Windows/Fonts/arial.ttf"

    - Possible keys:
    "opacity" - Opacity of text - <float, Range:0-1>
    "bg_opacity" - Opacity of background (box around text) - <float, Range:0-1>
    "bg_color" - Background color - <color>
    "bg_padding" - Background padding in pixels - <int>
    "x_offset" - offsets burnin vertically by entered pixels from border - <int>
    "y_offset" - offsets burnin horizontally by entered pixels from border - <int>
    - x_offset & y_offset should be set at least to same value as bg_padding!!
    "font" - Font Family for text - <font>
    "font_size" - Font size in pixels - <int>
    "font_color" - Color of text - <color>
    "frame_offset" - Default start frame - <int>
        - required IF start frame is not set when using frames or timecode burnins

    On initializing class can be set General options through "options_init" arg.
    General can be overriden when adding burnin

    '''
    TOP_CENTERED = ffmpeg_burnins.TOP_CENTERED
    BOTTOM_CENTERED = ffmpeg_burnins.BOTTOM_CENTERED
    TOP_LEFT = ffmpeg_burnins.TOP_LEFT
    BOTTOM_LEFT = ffmpeg_burnins.BOTTOM_LEFT
    TOP_RIGHT = ffmpeg_burnins.TOP_RIGHT
    BOTTOM_RIGHT = ffmpeg_burnins.BOTTOM_RIGHT

    options_init = {
        'opacity': 1,
        'x_offset': 5,
        'y_offset': 5,
        'bg_padding': 5,
        'bg_opacity': 0.5,
        'font_size': 42
    }

    def __init__(self, source, streams=None, options_init=None):
        if not streams:
            streams = _streams(source)

        super().__init__(source, streams)

        if options_init:
            self.options_init.update(options_init)

    def add_text(
        self, text, align, frame_start=None, frame_end=None, options=None
    ):
        """
        Adding static text to a filter.

        :param str text: text to apply to the drawtext
        :param enum align: alignment, must use provided enum flags
        :param int frame_start: starting frame for burnins current frame
        :param dict options: recommended to use TextOptions
        """
        if not options:
            options = ffmpeg_burnins.TextOptions(**self.options_init)

        options = options.copy()
        if frame_start is not None:
            options["frame_offset"] = frame_start

        # `frame_end` is only for meassurements of text position
        if frame_end is not None:
            options["frame_end"] = frame_end

        self._add_burnin(text, align, options, DRAWTEXT)

    def add_timecode(
        self, align, frame_start=None, frame_end=None, frame_start_tc=None,
        text=None, options=None
    ):
        """
        Convenience method to create the frame number expression.

        :param enum align: alignment, must use provided enum flags
        :param int frame_start:  starting frame for burnins current frame
        :param int frame_start_tc:  starting frame for burnins timecode
        :param str text: text that will be before timecode
        :param dict options: recommended to use TimeCodeOptions
        """
        if not options:
            options = ffmpeg_burnins.TimeCodeOptions(**self.options_init)

        options = options.copy()
        if frame_start is not None:
            options["frame_offset"] = frame_start

        # `frame_end` is only for meassurements of text position
        if frame_end is not None:
            options["frame_end"] = frame_end

        if not frame_start_tc:
            frame_start_tc = options["frame_offset"]

        if not text:
            text = ""

        if not options.get("fps"):
            options["fps"] = self.frame_rate

        if isinstance(frame_start_tc, str):
            options["timecode"] = frame_start_tc
        else:
            options["timecode"] = ffmpeg_burnins._frames_to_timecode(
                frame_start_tc,
                self.frame_rate
            )

        self._add_burnin(text, align, options, TIMECODE)

    def _add_burnin(self, text, align, options, draw):
        """
        Generic method for building the filter flags.
        :param str text: text to apply to the drawtext
        :param enum align: alignment, must use provided enum flags
        :param dict options:
        """

        final_text = text
        text_for_size = text
        if CURRENT_FRAME_SPLITTER in text:
            frame_start = options["frame_offset"]
            frame_end = options.get("frame_end", frame_start)
            if frame_start is None:
                replacement_final = replacement_size = str(MISSING_KEY_VALUE)
            else:
                replacement_final = "%{eif:n+" + str(frame_start) + ":d}"
                replacement_size = str(frame_end)

            final_text = final_text.replace(
                CURRENT_FRAME_SPLITTER, replacement_final
            )
            text_for_size = text_for_size.replace(
                CURRENT_FRAME_SPLITTER, replacement_size
            )

        resolution = self.resolution
        data = {
            'text': (
                final_text
                .replace(",", r"\,")
                .replace(':', r'\:')
            ),
            'color': options['font_color'],
            'size': options['font_size']
        }
        timecode_text = options.get("timecode") or ""
        text_for_size += timecode_text

        data.update(options)

        os_system = platform.system().lower()
        data_font = data.get("font")
        if not data_font:
            data_font = (
                resources.get_liberation_font_path().replace("\\", "/")
            )
        elif isinstance(data_font, dict):
            data_font = data_font[os_system]

        if data_font:
            data["font"] = data_font
            options["font"] = data_font
            if ffmpeg_burnins._is_windows():
                data["font"] = (
                    data_font
                    .replace(os.sep, r'\\' + os.sep)
                    .replace(':', r'\:')
                )

        data.update(
            ffmpeg_burnins._drawtext(align, resolution, text_for_size, options)
        )

        self.filters['drawtext'].append(draw % data)

        if options.get('bg_color') is not None:
            box = ffmpeg_burnins.BOX % {
                'border': options['bg_padding'],
                'color': options['bg_color'],
                'opacity': options['bg_opacity']
            }
            self.filters['drawtext'][-1] += ':%s' % box

    def command(self, output=None, args=None, overwrite=False):
        """
        Generate the entire FFMPEG command.

        :param str output: output file
        :param str args: additional FFMPEG arguments
        :param bool overwrite: overwrite the output if it exists
        :returns: completed command
        :rtype: str
        """
        output = '"{}"'.format(output or '')
        if overwrite:
            output = '-y {}'.format(output)

        filters = ''
        if self.filter_string:
            filters = '-vf "{}"'.format(self.filter_string)

        return (FFMPEG % {
            'input': self.source,
            'output': output,
            'args': '%s ' % args if args else '',
            'filters': filters
        }).strip()

    def render(self, output, args=None, overwrite=False, **kwargs):
        """
        Render the media to a specified destination.

        :param str output: output file
        :param str args: additional FFMPEG arguments
        :param bool overwrite: overwrite the output if it exists
        """
        if not overwrite and os.path.exists(output):
            raise RuntimeError("Destination '%s' exists, please "
                               "use overwrite" % output)

        is_sequence = "%" in output

        command = self.command(
            output=output,
            args=args,
            overwrite=overwrite
        )
        print("Launching command: {}".format(command))

        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        _stdout, _stderr = proc.communicate()
        if _stdout:
            for line in _stdout.split(b"\r\n"):
                print(line.decode("utf-8"))

        # This will probably never happen as ffmpeg use stdout
        if _stderr:
            for line in _stderr.split(b"\r\n"):
                print(line.decode("utf-8"))

        if proc.returncode != 0:
            raise RuntimeError(
                "Failed to render '{}': {}'".format(output, command)
            )
        if is_sequence:
            output = output % kwargs.get("duration")

        if not os.path.exists(output):
            raise RuntimeError(
                "Failed to generate this f*cking file '%s'" % output
            )


def example(input_path, output_path):
    options_init = {
        'opacity': 1,
        'x_offset': 10,
        'y_offset': 10,
        'bg_padding': 10,
        'bg_opacity': 0.5,
        'font_size': 52
    }
    # First frame in burnin
    start_frame = 2000
    # Options init sets burnin look
    burnin = ModifiedBurnins(input_path, options_init=options_init)
    # Static text
    burnin.add_text('My Text', ModifiedBurnins.TOP_CENTERED)
    # Datetime
    burnin.add_text('%d-%m-%y', ModifiedBurnins.TOP_RIGHT)
    # Start render (overwrite output file if exist)
    burnin.render(output_path, overwrite=True)


def burnins_from_data(
    input_path, output_path, data,
    codec_data=None, options=None, burnin_values=None, overwrite=True
):
    """This method adds burnins to video/image file based on presets setting.

    Extension of output MUST be same as input. (mov -> mov, avi -> avi,...)

    Args:
        input_path (str): Full path to input file where burnins should be add.
        output_path (str): Full path to output file where output will be
            rendered.
        data (dict): Data required for burnin settings (more info below).
        codec_data (list): All codec related arguments in list.
        options (dict): Options for burnins.
        burnin_values (dict): Contain positioned values.
        overwrite (bool): Output will be overriden if already exists,
            True by default.

    Presets must be set separately. Should be dict with 2 keys:
    - "options" - sets look of burnins - colors, opacity,...(more info: ModifiedBurnins doc)
                - *OPTIONAL* default values are used when not included
    - "burnins" - contains dictionary with burnins settings
                - *OPTIONAL* burnins won't be added (easier is not to use this)
        - each key of "burnins" represents Alignment, there are 6 possibilities:
            TOP_LEFT        TOP_CENTERED        TOP_RIGHT
            BOTTOM_LEFT     BOTTOM_CENTERED     BOTTOM_RIGHT
        - value must be string with text you want to burn-in
        - text may contain specific formatting keys (exmplained below)

    Requirement of *data* keys is based on presets.
    - "frame_start" - is required when "timecode" or "current_frame" ins keys
    - "frame_start_tc" - when "timecode" should start with different frame
    - *keys for static text*

    EXAMPLE:
    preset = {
        "options": {*OPTIONS FOR LOOK*},
        "burnins": {
            "TOP_LEFT": "static_text",
            "TOP_RIGHT": "{shot}",
            "BOTTOM_LEFT": "TC: {timecode}",
            "BOTTOM_RIGHT": "{frame_start}{current_frame}"
        }
    }

    For this preset we'll need at least this data:
    data = {
        "frame_start": 1001,
        "shot": "sh0010"
    }

    When Timecode should start from 1 then data need:
    data = {
        "frame_start": 1001,
        "frame_start_tc": 1,
        "shot": "sh0010"
    }
    """

    burnin = ModifiedBurnins(input_path, options_init=options)

    frame_start = data.get("frame_start")
    frame_end = data.get("frame_end")
    frame_start_tc = data.get('frame_start_tc', frame_start)

    stream = burnin._streams[0]
    if "resolution_width" not in data:
        data["resolution_width"] = stream.get("width", MISSING_KEY_VALUE)

    if "resolution_height" not in data:
        data["resolution_height"] = stream.get("height", MISSING_KEY_VALUE)

    if "fps" not in data:
        data["fps"] = get_fps(stream.get("r_frame_rate", "0/0"))

    # Check frame start and add expression if is available
    if frame_start is not None:
        data[CURRENT_FRAME_KEY[1:-1]] = CURRENT_FRAME_SPLITTER

    if frame_start_tc is not None:
        data[TIMECODE_KEY[1:-1]] = TIMECODE_KEY

    source_timecode = stream.get("timecode")
    if source_timecode is None:
        source_timecode = stream.get("tags", {}).get("timecode")

    if source_timecode is not None:
        data[SOURCE_TIMECODE_KEY[1:-1]] = SOURCE_TIMECODE_KEY

    for align_text, value in burnin_values.items():
        if not value:
            continue

        if isinstance(value, (dict, list, tuple)):
            raise TypeError((
                "Expected string or number type."
                " Got: {} - \"{}\""
                " (Make sure you have new burnin presets)."
            ).format(str(type(value)), str(value)))

        align = None
        align_text = align_text.strip().lower()
        if align_text == "top_left":
            align = ModifiedBurnins.TOP_LEFT
        elif align_text == "top_centered":
            align = ModifiedBurnins.TOP_CENTERED
        elif align_text == "top_right":
            align = ModifiedBurnins.TOP_RIGHT
        elif align_text == "bottom_left":
            align = ModifiedBurnins.BOTTOM_LEFT
        elif align_text == "bottom_centered":
            align = ModifiedBurnins.BOTTOM_CENTERED
        elif align_text == "bottom_right":
            align = ModifiedBurnins.BOTTOM_RIGHT

        has_timecode = TIMECODE_KEY in value
        # Replace with missing key value if frame_start_tc is not set
        if frame_start_tc is None and has_timecode:
            has_timecode = False
            print(
                "`frame_start` and `frame_start_tc`"
                " are not set in entered data."
            )
            value = value.replace(TIMECODE_KEY, MISSING_KEY_VALUE)

        has_source_timecode = SOURCE_TIMECODE_KEY in value
        if source_timecode is None and has_source_timecode:
            has_source_timecode = False
            print("Source does not have set timecode value.")
            value = value.replace(SOURCE_TIMECODE_KEY, MISSING_KEY_VALUE)

        key_pattern = re.compile(r"(\{.*?[^{0]*\})")

        missing_keys = []
        for group in key_pattern.findall(value):
            try:
                group.format(**data)
            except (TypeError, KeyError):
                missing_keys.append(group)

        missing_keys = list(set(missing_keys))
        for key in missing_keys:
            value = value.replace(key, MISSING_KEY_VALUE)

        # Handle timecode differently
        if has_source_timecode:
            args = [align, frame_start, frame_end, source_timecode]
            if not value.startswith(SOURCE_TIMECODE_KEY):
                value_items = value.split(SOURCE_TIMECODE_KEY)
                text = value_items[0].format(**data)
                args.append(text)

            burnin.add_timecode(*args)
            continue

        if has_timecode:
            args = [align, frame_start, frame_end, frame_start_tc]
            if not value.startswith(TIMECODE_KEY):
                value_items = value.split(TIMECODE_KEY)
                text = value_items[0].format(**data)
                args.append(text)

            burnin.add_timecode(*args)
            continue

        text = value.format(**data)
        burnin.add_text(text, align, frame_start, frame_end)

    ffmpeg_args = []
    if codec_data:
        # Use codec definition from method arguments
        ffmpeg_args = codec_data

    else:
        ffprobe_data = burnin._streams[0]
        codec_name = ffprobe_data.get("codec_name")
        if codec_name:
            if codec_name == "prores":
                tags = ffprobe_data.get("tags") or {}
                encoder = tags.get("encoder") or ""
                if encoder.endswith("prores_ks"):
                    codec_name = "prores_ks"

                elif encoder.endswith("prores_aw"):
                    codec_name = "prores_aw"
            ffmpeg_args.append("-codec:v {}".format(codec_name))

        profile_name = ffprobe_data.get("profile")
        if profile_name:
            # lower profile name and repalce spaces with underscore
            profile_name = profile_name.replace(" ", "_").lower()
            ffmpeg_args.append("-profile:v {}".format(profile_name))

        bit_rate = ffprobe_data.get("bit_rate")
        if bit_rate:
            ffmpeg_args.append("-b:v {}".format(bit_rate))

        pix_fmt = ffprobe_data.get("pix_fmt")
        if pix_fmt:
            ffmpeg_args.append("-pix_fmt {}".format(pix_fmt))

    # Use group one (same as `-intra` argument, which is deprecated)
    ffmpeg_args.append("-g 1")

    ffmpeg_args_str = " ".join(ffmpeg_args)
    burnin.render(
        output_path, args=ffmpeg_args_str, overwrite=overwrite, **data
    )


if __name__ == "__main__":
    print("* Burnin script started")
    in_data_json_path = sys.argv[-1]
    with open(in_data_json_path, "r") as file_stream:
        in_data = json.load(file_stream)

    burnins_from_data(
        in_data["input"],
        in_data["output"],
        in_data["burnin_data"],
        codec_data=in_data.get("codec"),
        options=in_data.get("options"),
        burnin_values=in_data.get("values")
    )
    print("* Burnin script has finished")
