import os,sys
from os.path import join, split, splitext, isdir, normpath
from subprocess import check_call,CalledProcessError
import Tkinter as tk
import ttk
import tkMessageBox as mbox
from time import time,sleep
from multiprocessing import Pool, Queue

#---------------------------------------------------------------
# init
if __name__ == '__main__':
  q = Queue()
  # make new log file
  LOGFILE = 'log_'+str(time())+'.txt'
  with open(LOGFILE,'w') as f:
    pass

#---------------------------------------------------------------
# clean up layout issues
def textclean(fp):
  'replace many spaces with one space'
  # read file
  with open(fp,'r') as f:
    orgtxt = f.read()
  # only one space allowed
  itertxt = iter(orgtxt)
  newtxt = ''
  space_counter = 0
  while True:
    # catch end of txt
    try:
      char  = next(itertxt)
    except StopIteration:
      break
    # increment counter
    if char == ' ':
      space_counter += 1
    # ignore multiple spaces
    if space_counter >= 2:
      # iter until char is not space
      char = next(itertxt)
      while char == ' ':
        # get next char if current char is ' '
        char = next(itertxt)
      # char is now not a space, add it to newtxt
      newtxt += char
      # reset counter
      space_counter = 0
    else:
      # else add the char
      newtxt += char
  # write new file
  with open(fp,'w') as f:
    f.write(newtxt)
  # done

#---------------------------------------------------------------
# handle PDF
def handlePDF(pathtup):
  'use pdftotext to convert pdf to a text file'
  # unpack
  pdf,txt = pathtup
  q = handlePDF.qu
  # name of pdf file
  f = split(pdf)[1]
  # default message to print
  msg = 'SUCCESS'
  # path to pdf tool
  toolpath = join( os.getcwd(), 'pdftotext.exe' )
  # encase in brackets
  _pdf = '"%s"'%pdf
  _txt = '"%s"'%txt
  # build command
  cmd = ' '.join( [toolpath,'-layout',_pdf,_txt] )
  # see if it works
  try:
    res = check_call(cmd,shell=True)
  except CalledProcessError as e:
    # return error msg
    msg = 'FAILED'
    retmsg = '\t'.join([msg,f])
    q.put( retmsg )
    return retmsg
  # didn't fail, so clean up text
  textclean(txt)
  # return message
  retmsg = '\t'.join([msg,f])
  q.put( retmsg )
  return retmsg

#---------------------------------------------------------------
# callback for completion
def poolcb(msgs):
  'callback func for pool.map_async()'
  with open(LOGFILE,'a') as f:
    while q.qsize() != 0:
      msg = q.get()
      f.write( msg + '\n' )
      print msg

#---------------------------------------------------------------
# proc initializer
def proc_init(q):
  handlePDF.qu = q

#---------------------------------------------------------------
# Button callback function

if __name__ == '__main__':
  RUNNING = False
  NPDFS = 0

def button_fn(cb=None):
  'Convert a PDF'
  global RUNNING,NPDFS

  # only run once
  if RUNNING:
    return
  else:
    RUNNING = True

  # number of procs
  nop = entry3.get()
  try:
    nop = int(nop)
  except ValueError:
    mbox.showerror('Value Error','Please enter an integer in the last field.')
    return

  # make multiproc pool, with initializer to allow queue access
  pool = Pool(initializer = proc_init,
              initargs    = [q,],
              processes   = min(32,nop))
  
  # pdf dir
  txt1 = entry1.get()
  ispath1 = isdir( txt1 )

  # output dir
  txt2 = entry2.get()
  ispath2 = isdir( txt2 )

  if not ispath1 or not ispath2:
    msg = 'PDF directory path is %s.\n'%('valid' if ispath1 else 'invalid')+\
          'Output directory path is %s.'%('valid' if ispath2 else 'invalid')
    mbox.showerror('Path error',msg)
    return
  
  # paths look okay
  pdfdir = normpath(txt1)
  outdir = normpath(txt2)

  # walk through top level of pdfdir and get pdf filenames
  w = os.walk(pdfdir)

  # next(w) returns a tuple ('root dir', [folder list], [file list])
  dir_tup = next(w)

  # filter out things that are not pdfs
  ispdf     = lambda x: True if x.endswith('pdf') else False
  pdfs      = filter(ispdf,dir_tup[2])

  # add full path name
  pathfix   = lambda x: join(dir_tup[0],x)
  _pdfs     = map(pathfix, pdfs)

  # num of pdfs
  NPDFS = len(_pdfs)

  # construct text file path
  txts      = [ join(outdir, splitext(split(pdf)[1])[0] + '.txt') for pdf in _pdfs]

  # send PDFs to be processed
  assert len(txts) == len(_pdfs)
  #print handlePDF( (_pdfs[9],txts[9]) )
  res = pool.map_async(handlePDF, zip(_pdfs,txts), callback=poolcb)

#---------------------------------------------------------------
# iterate the progress bar

##sofar = 0
##
##def update_progress(callback=None):
##  global sofar
##  # num of things in queue
##  n = q.qsize()
##  # catch divide by zero
##  if NPDFS == 0 or n==0:
##    root.after(100,update_progress)
##    return
##  #
##  if n >= sofar:
##    intv  = (n-sofar)/float(NPDFS)
##    sofar = n
##    pb.step(intv)
##  root.after(1000,update_progress)

#---------------------------------------------------------------
# Set up tkinter environment
if __name__ == '__main__':
  root = tk.Tk()
  w,h = root.winfo_screenwidth(), root.winfo_screenheight()
  winx = 500
  root.geometry('%dx81+%d+%d'%(winx,(w-winx)/2,h/2))
  root.resizable(1,0)
  root.bind('<Return>',button_fn)
  root.title('PDF to Text')
  root.iconbitmap('icon.ico')

  # Label 1 (pdf dir)
  label1 = tk.Label(root,text='Enter directory containing PDFs ',anchor=tk.E)
  label1.grid(row=1,column=1,sticky=tk.W)

  # Entry 1 (pdf dir)
  entry1 = tk.Entry(root)
  entry1.grid(row=1,column=2,sticky=tk.E+tk.W)
  entry1.focus_set()
  entry1.insert(0,'C:\\Users\\John\\Dropbox\\Public\\Code\\Python\\project\\pdftotext\\pdftotext\\pdfdir')

  # Label 2 (out dir)
  label2 = tk.Label(root,text='Enter directory to output text to ',anchor=tk.E)
  label2.grid(row=2,column=1,sticky=tk.W)

  # Entry 2 (out dir)
  entry2 = tk.Entry(root)
  entry2.grid(row=2,column=2,sticky=tk.E+tk.W)
  entry2.insert(0,'C:\\Users\\John\\Dropbox\\Public\\Code\\Python\\project\\pdftotext\\pdftotext\\txtdir')

  # Label 3 (proc num)
  label3 = tk.Label(root,text='Number of processes to spawn ',anchor=tk.E)
  label3.grid(row=3,column=1,sticky=tk.W)

  # Entry 3 (proc num)
  entry3 = tk.Entry(root)
  entry3.grid(row=3,column=2,sticky=tk.E+tk.W)
  entry3.insert(0,'16')

  # Progress Bar
  pb = ttk.Progressbar(orient=tk.HORIZONTAL, length=winx, mode='determinate')
  pb.grid(row=4,column=1,columnspan=3)

  # Button
  button = tk.Button(root,text='Go',width=5,command=button_fn)
  button.grid(row=1,column=3,rowspan=3,sticky=tk.W+tk.N+tk.S)

  # Weight middle column
  root.columnconfigure(2,weight=1)
  root.after(100,update_progress)
  root.mainloop()
