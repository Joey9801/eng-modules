from app import *
from flask import render_template, request, jsonify
import psycopg2, psycopg2.extras

@app.route('/')
def index():
    num_people = find_num_people()
    user = find_user(auth_dec.principal)
    return render_template('index.html',
                           user = user,
                           num_people = num_people)
            
            
@app.route('/update_modules', methods=['POST'])
def update_modules_post():
    crsid = auth_dec.principal
    try:
        modules = list(map(int, request.form.getlist("modules[]") ) )
        new_name = request.form["new_name"].title()
        valid, reasons = validate_modules(modules)
    except (ValueError, TypeError):
        valid = False
        print(request.form.getlist("modules[]"))
        reasons = ["Error while processing modules"]
    
    if not valid:
        return jsonify(valid=False, 
                       reasons=reasons), 400
                       
    person_query = 'SELECT * FROM people WHERE crsid=%s'
    name_query = 'UPDATE people SET name=%s WHERE crsid=%s'
    del_query = 'DELETE FROM choices WHERE person=%s'
    add_query = 'INSERT INTO choices (person, module) VALUES (%s, %s)'
    
    with psycopg2.connect("dbname=engmodules user=joe") as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute(person_query, (crsid,))
        user = cur.fetchone()
        uid = user['id']
        name = user['name']
        if new_name != name:
            cur.execute(name_query, (new_name, crsid))
        
        #remove all previous selection
        cur.execute(del_query, (uid,))
        
        #add in the new selection
        for module in modules:
            cur.execute(add_query, (uid, module))
        
        conn.commit()
    
    return jsonify(valid=True,
                   redirect="/view_modules"), 202
    
@app.route('/update_modules', methods=['GET'])
def update_modules_get():
    user = find_user(auth_dec.principal)
    num_people = find_num_people()
    return render_template('selection.html',
                           user = user,
                           modules = modules,
                           num_people = num_people)
     
                           
@app.route('/view_modules', methods=['GET'])
def view_modules():
    user = find_user(auth_dec.principal)
    num_people = find_num_people()
    with psycopg2.connect("dbname=engmodules user=joe") as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query1 = 'SELECT * FROM modules JOIN choices ON choices.module=modules.id ' \
                 'WHERE choices.person=%s'
        query2 = 'SELECT * FROM modules ' \
                 'WHERE id NOT IN (SELECT module FROM choices WHERE person=2)'
        cur.execute(query1, (user['id'],))
        user['modules'] = cur.fetchall();
        
        cur.execute(query2, (user['id'],))
        other_modules = cur.fetchall();
    return render_template('view.html',
                           user = user,
                           other_modules = other_modules,
                           num_people = num_people)
                           
@app.route('/module/<int:module>/namelist.json', methods=['GET'])
def get_user_list(module):
    query = 'SELECT crsid, name FROM choices c JOIN people p on c.person=p.id ' \
            'WHERE c.module=%s'
    with psycopg2.connect("dbname=engmodules user=joe") as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, (module,))
        namelist = cur.fetchall()
    
    return jsonify(namelist=namelist)
                           
                           
def find_user(crsid):
    with psycopg2.connect("dbname=engmodules user=joe") as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT COUNT(*) FROM people WHERE crsid=%s', (crsid,))
        exists = bool(cur.fetchone()['count'])
        
        if not exists:
            cur.execute('INSERT INTO people (crsid, name) VALUES (%s, %s) RETURNING *', (crsid, crsid))
            user = cur.fetchone()
        
        else:
            cur.execute('SELECT * FROM people WHERE crsid=%s', (crsid,))
            user = cur.fetchone()
            
            cur.execute('SELECT COUNT(*) FROM choices WHERE person=%s', (user['id'],))
            if not cur.fetchone()['count']:
                user['new'] = True
            else:
                user['new'] = False
            
            cur.execute('SELECT module FROM choices WHERE person=%s', (user['id'],))
            user['modules'] = [x['module'] for x in cur.fetchall()]
                
    return user

def find_num_people():
    with psycopg2.connect("dbname=engmodules user=joe") as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT COUNT(person) FROM (SELECT DISTINCT person FROM choices) AS temp;')
        num_people = cur.fetchone()['count']
    return num_people

def validate_modules(modules):
    valid = True
    reasons = list()
    if len(modules) > 10:
        valid = False
        reasons.append('Too many modules')
    return valid, reasons
    #TODO, other validation stuff... maybe
