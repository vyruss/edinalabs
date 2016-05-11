#!/usr/bin/env python
# Our imports and database connection
import sys
import io
import json
import xmltodict
import psycopg2
import psycopg2.extras
import datetime
import cStringIO  # Faster than simple Python string I/O

conn = psycopg2.connect(database='marc', user='marc')
conn.set_isolation_level(  # For faster INSERTs
    psycopg2.extensions.ISOLATION_LEVEL_READ_UNCOMMITTED)
cur = conn.cursor()
count = 0
buffr = cStringIO.StringIO()
itercount = 0

# Our XML event callback handler function
def handle(_, item):
    global conn, cur, count, itercount, buffr
    out = {}
    tag = {}
    subfields = []
    for i,j in item.items():  # Iterate over the XML stream
        if i == 'leader':
            out[i]=j
        elif i == 'controlfield':
            for k in j:
                if '#text' in k:
                    out[k['@tag']] = k['#text']
                else:
                    out[k['@tag']] = None
        else:  # if i == 'datafield' :
            for k in j:  # Nested loop to iterate over subfields
                if type(k['subfield']) != list:
                    l = k['subfield']
                    if '#text' in l:
                        subfields = [{l['@code']:l['#text']}]
                    else:
                        subfields = [{l['@code']:None}]
                else:
                    for l in k['subfield']:
                        if '#text' in l:
                            subfields.append({l['@code']:l['#text']})
                        else:
                            subfields.append({l['@code']:None})
                tag['ind1'] = k['@ind1']
                tag['ind2'] = k['@ind2']
                tag['subfields'] = subfields
                if k['@tag'] in out.keys():
                    out[k['@tag']].append(tag)
                else:
                    out[k['@tag']] = [tag]
                subfields = []
                tag = {}
    # So let's output this dict we've created into JSON
    tmp = json.dumps(out).replace('\\','\\\\')  # Watch out!
    buffr.write(tmp)
    buffr.write('\n')
    count += 1
    if count % 10000 == 0:
        count = 0
        buffr.seek(0)
        cur.copy_from(buffr,'suncat')  # Should be fast
        conn.commit()
        buffr = cStringIO.StringIO()
        itercount += 1
        timeb = datetime.datetime.now()
        print itercount*10000,'records inserted in',timeb-timea
    return True

# Our main function to open and parse the XML file
def convert(xml_file):
    with open(xml_file, "rb") as f:  # Notice "rb" mode!
        xmltodict.parse(f, item_depth=3,
                        item_callback=handle,
                        process_namespaces=False,
                        xml_attribs=True,
                        strip_whitespace=False)
        # Iterate once more for the last < 10000 items
        buffr.seek(0)
        cur.copy_from(buffr,'suncat')
        conn.commit()
        print count+itercount*10000,'records inserted.'
        return

if __name__ == "__main__":
   cur.execute('DROP TABLE suncat')
   cur.execute('CREATE TABLE suncat (data JSONB)')
   timea = datetime.datetime.now()
   convert(sys.argv[1])  # Grab filename from cmd line arg
   cur.copy_from(buffr,'suncat')
   conn.commit()
   conn.close()
   timeb = datetime.datetime.now()
   print 'TOTAL time was:', timeb - timea
