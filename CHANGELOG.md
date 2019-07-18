# PyExifTool Changelog

Current dates are in PST/PDT

Date (Timezone)              | Version | Comment
---------------------------- | ------- | -------
07/17/2019 12:26:16 AM (PDT) | 0.1     | Source was pulled directly from https://github.com/smarnach/pyexiftool with a complete bare clone to preserve all history.  Because it's no longer being updated, I will pull all merge requests in and make updates accordingly
07/17/2019 12:50:20 AM (PDT) | 0.1     | Convert leading spaces to tabs
07/17/2019 12:52:33 AM (PDT) | 0.1.1   | Merge [Pull request #10 "add copy_tags method"](https://github.com/smarnach/pyexiftool/pull/10) by [Maik Riechert (letmaik) Cambridge, UK](https://github.com/letmaik) on May 28, 2014<br> *This adds a small convenience method to copy any tags from one file to another. I use it for several month now and it works fine for me.*
07/17/2019 01:05:37 AM (PDT) | 0.1.2   | Merge [Pull request #25 "Added option for keeping print conversion active. #25"](https://github.com/smarnach/pyexiftool/pull/25) by [Bernhard Bliem (bbliem)](https://github.com/bbliem) on Jan 17, 2019<br> *For some tags, disabling print conversion (as was the default before) would not make much sense. For example, if print conversion is deactivated, the value of the Composite:LensID tag could be reported as something like "8D 44 5C 8E 34 3C 8F 0E". It is doubtful whether this is useful here, as we would then need to look up what this means in a table supplied with exiftool. We would probably like the human-readable value, which is in this case "AF-S DX Zoom-Nikkor 18-70mm f/3.5-4.5G IF-ED".*<br>*Disabling print conversion makes sense for a lot of tags (e.g., it's nicer to get as the exposure time not the string "1/2" but the number 0.5). In such cases, even if we enable print conversion, we can disable it for individual tags by appending a # symbol to the tag name.*
07/17/2019 01:20:15 AM (PDT) | 0.1.3   | Merge with slight modifications to variable names for clarity (sylikc) [Pull request #27 "Add "shell" keyword argument to ExifTool initialization"](https://github.com/smarnach/pyexiftool/pull/27) by [Douglas Lassance (douglaslassance) Los Angeles, CA](https://github.com/douglaslassance) on 5/29/2019<br>*On Windows this will allow to run exiftool without showing the DOS shell.*<br>**This might break Linux but I don't know for sure**<br>Alternative source location with only this patch: https://github.com/blurstudio/pyexiftool/tree/shell-option
07/17/2019 01:24:32 AM (PDT) | 0.1.4   | Merge [Pull request #19 "Correct dependency for building an RPM."](https://github.com/smarnach/pyexiftool/pull/19) by [Achim Herwig (Achimh3011) Munich, Germany](https://github.com/Achimh3011) on Aug 25, 2016<br>**I'm not sure if this is entirely necessary, but merging it anyways**
07/17/2019 02:09:40 AM (PDT) | 0.1.5   | Merge [Pull request #15 "handling Errno:11 Resource temporarily unavailable"](https://github.com/smarnach/pyexiftool/pull/15) by [shoyebi](https://github.com/shoyebi) on Jun 12, 2015
07/18/2019 03:40:39 AM (PDT) | 0.1.6   | set_tags and UTF-8 cmdline - Merge in the first set of changes by Leo Broska related to [Pull request #5 "add set_tags_batch, set_tags + constructor takes added options"](https://github.com/smarnach/pyexiftool/pull/5) by [halloleo](https://github.com/halloleo) on Aug 1, 2012<br> but this is sourced from [jmathai/elodie's 6114328 Jun 22,2016 commit](https://github.com/jmathai/elodie/blob/6114328f325660287d1998338a6d5e6ba4ccf069/elodie/external/pyexiftool.py)
07/18/2019 03:59:02 AM (PDT) | 0.1.7   | Merge another commit fromt he jmathai/elodie [zserg on Mar 12, 2016](https://github.com/jmathai/elodie/blob/af36de091e1746b490bed0adb839adccd4f6d2ef/elodie/external/pyexiftool.py)<br> seems to do UTF-8 encoding on set_tags
07/18/2019 04:01:18 AM (PDT) | 0.1.7   | minor change it looks like a rename to match PEP8 coding standards by [zserg on Aug 21, 2016](https://github.com/jmathai/elodie/blob/ad1cbefb15077844a6f64dca567ea5600477dd52/elodie/external/pyexiftool.py)
07/18/2019 04:05:36 AM (PDT) | 0.1.8   | [Fallback to latin if utf-8 decode fails in pyexiftool.py](https://github.com/jmathai/elodie/commit/fe70227c7170e01c8377de7f9770e761eab52036#diff-f9cf0f3eed27e85c9c9469d0e0d431d5) by [jmathai](https://github.com/jmathai/elodie/commits?author=jmathai) on Sep 7, 2016
07/18/2019 04:14:32 AM (PDT) | 0.1.9   | Merge the test cases from the [Pull request #5 "add set_tags_batch, set_tags + constructor takes added options"](https://github.com/smarnach/pyexiftool/pull/5) by [halloleo](https://github.com/halloleo) on Aug 1, 2012
07/18/2019 04:34:46 AM (PDT) | 0.3.0   | changed the setup.py licensing and updated the version numbering as in changelog<br>changed the version number scheme, as it appears the "official last release" was 0.2.0 tagged.  There's going to be a lot of things broken in this current build, and I'll fix it as they come up.  I'm going to start playing with the library and the included tests and such.  <br>There's one more pull request #11 which would be pending, but it duplicates the extra arguments option.  <br>I'm also likely to remove the print conversion as it's now covered by the extra args.  I'll also rename some variable names with the addedargs patch<br>**for my changes (sylikc), I can only guarantee they will work on Python 3.7, because that's my environment... and while I'll try to maintain compatibility, there's no guarantees**
07/18/2019 05:06:19 AM (PDT) | 0.3.1   | make some minor tweaks to the naming of the extra args variable.  The other pull request 11 names them params, and when I decide how to merge that pull request, I'll probably change the variable names again.



# Changes around the web

Check for changes at the following resources to make sure we have the latest and greatest.  After all, I'm "unofficially forked" here offline.  I intend to publish the changes once I get it into a working state for my DV Suite

(last checked 7/17/2019 all)
search "pyexiftool github" to see if you find any more random ports/forks
check for updates https://github.com/smarnach/pyexiftool/pulls
check for updates https://github.com/blurstudio/pyexiftool/tree/shell-option (#27)
check for updates https://github.com/RootLUG/pyexiftool (#27)
check for updates https://pypi.org/project/PyExifTool/0.1.1/#files (#15)
check for updates on elodie https://github.com/jmathai/elodie/commits/master/elodie/external/pyexiftool.py
check for new open issues https://github.com/smarnach/pyexiftool/issues?q=is%3Aissue+is%3Aopen

