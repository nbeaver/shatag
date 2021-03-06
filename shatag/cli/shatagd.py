#!/usr/bin/env python3
# Copyright 2011 Maxime Augier
# Distributed under the terms of the GNU General Public License

import argparse
import asyncore
import os
import pyinotify
import shatag
import sys

def main():

    config = shatag.Config()
    
    parser = argparse.ArgumentParser( description='Monitors files with inotify and automatically update')
    parser.add_argument('-u','--update', action='store_true', help='Only update already tagged files')
    parser.add_argument('-p','--put', action='store_true', help='Send new hashes to database')
    parser.add_argument('-v','--verbose', action='store_true', help='report missing/invalid checksums')
    parser.add_argument('-b','--backend', metavar='BACKEND', help='backend for local tag storage', default=config.backend)
    parser.add_argument('-r','--recursive', action='store_true', help='watch recursively')
    parser.add_argument('-d','--daemon', action='store_true', help='daemonize')
    
    parser.add_argument('paths', metavar='PATH', nargs='+', help='paths to monitor')
    
    args = parser.parse_args()
    
    backend = shatag.backend(args.backend)
    store = None
    if args.put:
        store = shatag.Store(name=config.name, url=config.database)
        print("shatagd: updating database {0} with name {1}".format(config.database,store.name), file=sys.stderr)
    	
    
    class Handler(pyinotify.ProcessEvent):
        def process_IN_CLOSE_WRITE(self, evt):
            try:
                file = backend.file(evt.pathname)
                
    
                if args.update:
                    file.update()
                else:
                    file.tag()
    
                if args.verbose:
                    print(evt.pathname)
    
                if args.put:
                    store.put(file)
                    store.commit()
    
            except IOError as e:
                print ('shatagd: "{0}": IOError {1}: {2}'.format(filename, e.errno, e.strerror), file=sys.stderr) 
    
            except OSError as e:
                print ('shatagd: {0}'.format(e), file=sys.stderr)
    
    wm = pyinotify.WatchManager()
    nf = pyinotify.AsyncNotifier(wm, Handler())
    nf.coalesce_events()
    
    for path in args.paths:
        if (args.daemon and path[0] != '/'):
            print("Warning: relative path {0} ignored in daemon mode. Use absolute paths.".format(path), file=sys.stderr)
        else:
            wm.add_watch(path, pyinotify.IN_CLOSE_WRITE | pyinotify.IN_CREATE, rec=args.recursive, auto_add=args.recursive)
            
    
    if(args.daemon):
        
        print("Daemonizing...",file=sys.stderr)
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
    
            os.chdir("/")
            os.setsid()
            os.umask(0)
    
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            print("OS Error: {0}".format(e), file=sys.stderr)
            sys.exit(1)
    
    asyncore.loop()
