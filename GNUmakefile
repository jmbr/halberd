# GNUmakefile
# $Id: GNUmakefile,v 1.5 2004/02/13 01:29:54 rwx Exp $

# Copyright (C) 2004 Juan M. Bello Rivas <rwx@synnergy.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


srcdir := .
hlbddir := $(srcdir)/hlbd
docdir := $(srcdir)/doc/api
testdir := $(srcdir)/test


PYTHON := /usr/local/bin/python
EPYDOC := /usr/local/bin/epydoc
CTAGS := /usr/local/bin/ctags
CVS2CL := /usr/local/bin/cvs2cl.pl
SHTOOLIZE := /usr/local/bin/shtoolize
SHTOOL := $(srcdir)/shtool

versionfile := $(hlbddir)/version.py

SCRIPTS := halberd.py
MODULES := $(filter-out $(version-file), $(wildcard $(hlbddir)/*.py)) $(wildcard $(hlbddir)/clues/*.py)
SOURCES := $(SCRIPTS) $(MODULES)
TEST_SOURCES = $(wildcard $(testdir)/*.py)


build: $(SOURCES)
	$(PYTHON) setup.py build

clean:
	rm -rf $(srcdir)/build
	rm -f *.py[co] $(hlbddir)/*.py[co] $(hlbddir)/clues/*.py[co] $(testdir)/*.py[co]

dist: distclean doc ChangeLog
	$(PYTHON) setup.py sdist

distclean: clobber clean
	rm -f $(srcdir)/{tags,MANIFEST,ChangeLog}
	rm -rf {$(docdir),$(srcdir)/dist}

check: $(TEST_SOURCES)
	$(PYTHON) -c 'import test'

doc: $(filter-out hlbd/version.py, $(MODULES))
	$(EPYDOC) -o $(docdir) $^

tags: clobber $(SOURCES)
	$(CTAGS) -R

clobber:
	rm -f *.bak $(srcdir)/*~ $(hlbddir)/*~ $(hlbddir)/clues/*~ $(testdir)/*~

incversion: shtool
	$(SHTOOL) version -l python -n halberd -i l $(versionfile)

shtool:
	$(SHTOOLIZE) -o $@ version

ChangeLog: $(SOURCES) $(TEST_SOURCES)
	$(CVS2CL)


.PHONY: clean dist distclean clobber check incversion doc
