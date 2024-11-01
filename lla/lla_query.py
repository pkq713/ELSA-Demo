#!/usr/bin/env python

#la-query.py -- script to perform query task for LSA package

#License: BSD

#Copyright (c) 2008 Li Charles Xia
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions
#are met:
#1. Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#2. Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#3. The name of the author may not be used to endorse or promote products
#   derived from this software without specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
#IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
#OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
#INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
#THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#public libs
import argparse, sys, os, csv, re
import numpy as np
try:
  # installed 
  from lsa import laio
  from lsa import lsalib
except ImportError:
  # debug
  from . import laio
  from . import lsalib
import lsa

rpy_import=False
#try:
#  import rpy2
#  import rpy2.rlike.container as rlc
#  import rpy2.robjects as ro
#  from rpy2.robjects.numpy2ri import numpy2ri
#  ro.conversion.py2ri = numpy2ri
#  r = ro.r
#  #print '''setwd("%s")''' % os.environ.get('PWD')
#  r('''setwd("%s")''' % os.environ.get('PWD'))
#  #r('''library(graphics)''')
#  #r('''library(gplots)''')
#except ImportError:
#  rpy_import=False
#  print >>sys.stderr, "IMPORTANT!!!: R and rpy2 are not working on this system"
#  print >>sys.stderr, "IMPORTANT!!!: This script is only workable with R and rpy2"
#  exit()

def main():

  __script__ = "la_query"
  version_desc = lsalib.safeCmd('lsa_version')
  version_print = "%s (rev: %s) - copyright Li Charlie Xia, lcxia@scut.edu.cn" \
    % (__script__, version_desc)
  print(version_print, file=sys.stderr)

  # define arguments: delayLimit, fillMethod, permuNum
  parser = argparse.ArgumentParser(description="Auxillary tool to new LSA package for querying la results")

  parser.add_argument("rawFile1", metavar= "rawFile1", type=argparse.FileType('r'), help="the raw lsaq file,get it from 'lsa_query'")
  parser.add_argument("rawFile2", metavar= "rawFile2", type=argparse.FileType('r'), help="the raw lat file,get it from 'la_compute'")
  parser.add_argument("rawFile3", metavar= "rawFile3", type=argparse.FileType('r'), help="the node information file,like:Domain,6Letter,Class....")
  parser.add_argument("rawFile4", metavar= "rawFile4", type=argparse.FileType('r'), help="the original time series file,Used to screen out some nodes what we need")
  parser.add_argument("newnodeFile", metavar= "newnodeFile",
                      help="This file contains the contents of third files and add the information of the m_x_y node, and added at the end of a column 'tag'")
  parser.add_argument("entryFile", metavar= "entryFile", help="the query result file,and add 'tag' column")

  parser.add_argument("-q", "--queryLine", dest="queryLine", default='(!la$P>0.01)&(la$Q<0.01)',
                      help="specify the highest pValue threshold for querying, default: None \n \
                        formatting a query: \n \
                        '[!]la$Key1[>,<,>=,<=,==,!=]V1[|,&][!]la$Key2[>,<,>=,<=,==,!=]V2[|,&]...' \n \
                        and any groupings using '(' and ')' default: \n \
                        '(!la$P>0.01)&(la$Q<0.01)'") 
  parser.add_argument("-x", "--xgmmlFile", dest="xgmmlFile", default="",
                      help="if specified, will also produce a XGMML format file for cytoscape")
  parser.add_argument("-s", "--sifFile", dest="sifFile", default="",
                      help="if specified, will also produce a SIF format file for backward compatibility")
  arg_namespace = parser.parse_args()

  #get the arguments
  print("la_query ($Revision$) - copyright Li Charlie Xia, lixia@stanford.edu", file=sys.stderr)
  print("learning arguments...", file=sys.stderr)
  
  rawFile1 = vars(arg_namespace)['rawFile1']
  rawFile2 = vars(arg_namespace)['rawFile2']
  rawFile3 = vars(arg_namespace)['rawFile3']
  rawFile4 = vars(arg_namespace)['rawFile4']
  newnodeFile = vars(arg_namespace)['newnodeFile']
  entryFile = vars(arg_namespace)['entryFile']
  queryLine = vars(arg_namespace)['queryLine']
  print("q=", queryLine)
  xgmmlFile = vars(arg_namespace)['xgmmlFile']
  sifFile = vars(arg_namespace)['sifFile']
  analysisTitle = os.path.basename(rawFile4.name)
  rawFile1.close()
  rawFile2.close()
  rawFile3.close()
  rawFile4.close()
  ds = analysisTitle.split('.',3)
  dsTitle = '.'.join(ds[0:3]) 


  print(dsTitle)
  print("reading the lsatable...", file=sys.stderr)
  r('''lsaq <- read.delim("%s")''' % (rawFile1.name))
  r('''la <- read.delim("%s")''' % (rawFile2.name))
  r('''nodeinfor <- read.delim("%s")''' % (rawFile3.name))  
  r('''nodelist <- read.delim("%s")''' % (rawFile4.name))
  try:
    print("querying the lsatable...", file=sys.stderr)
    r('''la_select <- la[%s,]''' % queryLine)
  except ValueError:
    print("error query formatting, try again", file=sys.stderr)
    quit()
  la_size=r('''dim(la_select)''')[0]
  lsaq_size=r('''dim(lsaq)''')[0]
  nodeinfor_size=r('''dim(nodeinfor)''')[0]
  nodelist_size=r('''dim(nodelist)''')[0]
  print("writing up result file...")
  laio.writeTable(laio.tryIO(entryFile,'w'), laio.tolaq(r.la_select, la_size, dsTitle))
  print("writing up new node information file...")
  laio.writeTable(laio.tryIO(newnodeFile,'w'), laio.tonewnode(r.la_select, la_size, r.lsaq, lsaq_size, r.nodeinfor, nodeinfor_size, r.nodelist, nodelist_size, dsTitle))
  # try:
  #  print >>sys.stderr, "writing up result file..."
  # r('''write.table( la_select, file="%s", quote=FALSE, row.names=FALSE, sep='\t' )''' % entryFile.name)
  # except ValueError:
  #  print >>sys.stderr, "no entry selected, try again"
  # quit()

  #rpy2 and R interfacing debug
  #print r.lsa_select
  #print r('''dim(lsa_select)''')[0]
  #print r.lsa_select.rx(1, True)
  #print tuple(r['colnames'](r.lsa_select))
  #print tuple(r['as.character'](r.lsa_select.rx(3, True)))
  #print tuple(r.lsa_select.rx(1, True)[2])[0]
  #print r['''as.character'''](r.lsa_select.rx(1, True)[0])[0]
  #print tuple(r.lsa_select.rx(1, True)[0])

  if xgmmlFile != "":
    print("filtering result as a XGMML file for visualization such as cytoscape...", file=sys.stderr)
    print(laio.LA_Xgmml2(r.la_select, la_size, r.lsaq, lsaq_size, r.nodeinfor, nodeinfor_size, r.nodelist, nodelist_size, dsTitle), file=laio.tryIO(xgmmlFile,'w'))

  if sifFile != "":
    print("filtering result as a SIF file for visualization such as cytoscape...", file=sys.stderr)
    laio.writeTable(laio.tryIO(sifFile,'w'), laio.toSif(r.la_select, la_size, r.lsaq, lsaq_size, r.nodelist, nodelist_size, analysisTitle))


  print("finishing up...", file=sys.stderr)
  print("Thank you for using lsa-query, byebye!", file=sys.stderr)

if __name__=="__main__":
  main()
  exit(0)
