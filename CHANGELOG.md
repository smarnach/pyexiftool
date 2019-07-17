# PyExifTool Changelog

Current dates are in PST/PDT

Date (Timezone)              | Version | Comment
---------------------------- | ------- | -------
07/17/2019 12:26:16 AM (PDT) | 0.1     | Source was pulled directly from https://github.com/smarnach/pyexiftool with a complete bare clone to preserve all history.  Because it's no longer being updated, I will pull all merge requests in and make updates accordingly
07/17/2019 12:50:20 AM (PDT) | 0.1     | Convert leading spaces to tabs
07/17/2019 12:52:33 AM (PDT) | 0.1.1   | Merge [Pull request #10 "add copy_tags method"](https://github.com/smarnach/pyexiftool/pull/10) by [Maik Riechert (letmaik) Cambridge, UK](https://github.com/letmaik) on May 28, 2014<br> *This adds a small convenience method to copy any tags from one file to another. I use it for several month now and it works fine for me.*
07/17/2019 01:05:37 AM (PDT) | 0.1.2   | Merge [Pull request #25 "Added option for keeping print conversion active. #25"](https://github.com/smarnach/pyexiftool/pull/25) by [Bernhard Bliem (bbliem)](https://github.com/bbliem) on Jan 17, 2019<br> *For some tags, disabling print conversion (as was the default before) would not make much sense. For example, if print conversion is deactivated, the value of the Composite:LensID tag could be reported as something like "8D 44 5C 8E 34 3C 8F 0E". It is doubtful whether this is useful here, as we would then need to look up what this means in a table supplied with exiftool. We would probably like the human-readable value, which is in this case "AF-S DX Zoom-Nikkor 18-70mm f/3.5-4.5G IF-ED".*<br>*Disabling print conversion makes sense for a lot of tags (e.g., it's nicer to get as the exposure time not the string "1/2" but the number 0.5). In such cases, even if we enable print conversion, we can disable it for individual tags by appending a # symbol to the tag name.*




