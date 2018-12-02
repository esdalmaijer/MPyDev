MPyDev
======

Version: 1.0.0
Date: 2018-12-02

This is a Python wrapper for [BIOPAC](http://www.biopac.com/)'s mpdev libraries,
and it should work with the MP150, MP36R, and MP160. For the latter, make sure
that your mpdev.dll version is up to date.


Installation
------------

1) Click the big green 'Clone/Download' button, then select 'Download ZIP'.
2) Unzip the downloaded archive.
3) Copy the file `mpydev.py` to a place from which you can import it, for example the `site-packages` directory of your Python installation, or the directory in which you store your experiment script.
4) Profit.


Example Usage
-------------

An example script can be found in `pygame_example.py`.


FAQ
---

**Your thing doesn't work!**
*Do you have mpdev.dll installed and/or within the directory that mpydev.py is in?*

**Your thing _still_ doesn't work!**
*Are you sure you're using the right version of mpdev.dll for your BIOPAC device?*

**IT STILL DOESNT WORK!!**
*Are you running Ackknowledge in the background? Please close down that software before running a script that uses MPyDev.*

**I don't have mpdev.dll, can you give it to me?**
*Unfortunately not. Please ask BIOPAC Systems for the file. It's proprietary software, and part of their SDK. You'll need to buy it from them directly.*


Boring Stuff
------------

All Python bits are developed by Edwin Dalmaijer. The required mpdev.dll file is
a proprietary library, created by [BIOPAC Systems, Inc.](http://www.biopac.com/).

MPyDev is open source software and therefore free to use and modify at will.
Warranty, however, is NOT given. If this software fails, causes your computer
to blow up, your spouse to leave you, your toilet to clog and/or the entire
supply of nuclear missles on earth to launch, or anything else that you might
want to blame on us, the author(s) CANNOT IN ANY WAY be held responsible.

MPyDev was released under the GNU Public License (version 3), of which you
should have received a copy of together with the software:

    MPyDev is Python software to communicate via UDP with BioPac devices.
    Copyright (C) 2014 Edwin S. Dalmaijer

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>

