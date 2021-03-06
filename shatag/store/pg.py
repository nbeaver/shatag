#!/usr/bin/env python3
# Copyright 2010 Maxime Augier
# Distributed under the terms of the GNU General Public License

import shatag
import psycopg2

class PgStore(shatag.base.SQLStore):
    """A postgresql store using psycopg2."""
    def __init__(self, url=None, name=None):
        db = psycopg2.connect(url[3:])
        self.db = db

        cursor = db.cursor()
        self.cursor = cursor

        super(PgStore,self).__init__(url, name)

        try:
            cursor.execute('create table contents(hash varchar(64), name varchar(50), path varchar(100), primary key (name, path))')
            cursor.execute('create index content_hash on contents(hash)')
        except psycopg2.ProgrammingError:
            db.rollback()

    # reimplementing these because psycopg2 does not handle classic placeholders correctly
    def clear(self, base='/',name=None):
        if name is None:
            name = self.name
        self.cursor.execute('delete from contents where name = %(name)s and substr(path,1,length(%(base)s)) like %(base)s', {'name': name, 'base': base})
        return self.cursor.rowcount


    def record(self, name, path, tag):
        d = {'name': name, 'path': path, 'tag':tag }
        self.cursor.execute('delete from contents where name = %(name)s and path = %(path)s', d)
        self.cursor.execute('insert into contents(hash,name,path) values(%(tag)s,%(name)s,%(path)s)', d)

    def fetch(self,hash):
        self.cursor.execute('select name,path from contents where hash = %(hash)s', {'hash':hash})
        return self.cursor 

