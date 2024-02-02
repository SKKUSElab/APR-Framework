import argparse
import sqlite3

from src.core import APR, Prioritization
from src.execution import Tester, Preprocess
from src.utils import Randoms, regularize, relative_patch_size, divide

def make_query(cur, table, table_dict, foreign=None):
    cur.execute(f'SELECT COUNT(*) FROM sqlite_master WHERE name="{table}"')
    if cur.fetchone()[0] == 0:
        create_query = ", ".join([f'{key} {value}' for key, value in table_dict.items()])
        if foreign: create_query += f', {foreign}'
        cur.execute(f'CREATE TABLE {table} ({create_query});')
    insert_query = ", ".join([f':{key}' for key in table_dict.keys()])
    query = f'INSERT INTO {table} VALUES({insert_query});'
    _query = {key:None for key in table_dict.keys()}
    return query, _query

def save_db(con, cur, query, _query):
    cur.execute(query, _query)
    _query = {key:None for key in _query.keys()}
    con.commit()
    return _query


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--project', type=int, default=1, required=True,
                        help="The number of project")
    parser.add_argument('-t', '--timeout', type=int, default=1,
                        help="Set timeout for compile program, default is 1sec")
    parser.add_argument('-g', '--generations', type=int, default=10,
                        help="Number of generations, default is 10")
    parser.add_argument('-s', '--seed', type=int, default=None,
                        help="Set start of random seed value, default is None")
    args = parser.parse_args()


    """Settings"""
    # Argument Parse
    project = args.project
    generations = args.generations
    seed = args.seed
    Randoms.seed = seed

    # Set DB
    dbfile = 'db.sqlite3'
    con = sqlite3.connect(dbfile)
    cur = con.cursor()

    # Get Instance
    corrects = f'SELECT * FROM instance WHERE project_id={project} AND solution={True}'
    cur.execute(corrects)
    correct_programs = {}
    for row in cur:
        correct_programs[row[0]] = row[2]
    cur = con.cursor()
    buggys = f'SELECT * FROM instance WHERE project_id={project} AND solution={False}'
    cur.execute(buggys)
    buggy_programs = {}
    for row in cur:
        buggy_programs[str(row[0])] = row[2]
    cur = con.cursor()
    testcases = f'SELECT * FROM testcase WHERE project_id={project}'
    cur.execute(testcases)
    testcases = []
    for row in cur:
        tc = {}
        tc['testcase_no'] = row[2]
        tc['input_tc'] = row[3]
        tc['output_tc'] = row[4]
        testcases.append(tc)
    cur = con.cursor()

    # CREATE 'run' Table
    table = 'run'.lower()
    table_dict = {
            'id':'INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL',
            'project_id': 'INTEGER NOT NULL',
            'seed':'INTEGER',
    }
    foreign = 'FOREIGN KEY (project_id) REFERENCES project(id)'
    query, _query = make_query(cur, table, table_dict, foreign)
    _query['project_id'] = project
    _query['seed'] = seed
    save_db(con, cur, query, _query)
    cur.execute("SELECT last_insert_rowid()")
    run_id = cur.fetchone()[0]
    cur = con.cursor()
    con.close()

    """Running APR-Framework"""
    ## Preprocessing
    tester = Tester(testcases, args.timeout)
    preproc = Preprocess(tester)
    preproc.run(buggy_programs)

    ## Run APR-Framework
    apr = APR(preproc, dbfile, foreign_id=run_id)
    solutions = apr.run(buggy_programs, pop_size=len(buggy_programs), generations=generations)
    prior = Prioritization(buggy_programs)
    patches = prior.run(solutions)
    

    """Save Results"""
    dbfile = 'db.sqlite3'
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    # CREATE 'result' Table
    table = 'result'.lower()
    table_dict = {'run_id':'INTEGER NOT NULL',
                  'instance_id':'INTEGER NOT NULL',
                  'solution':'BLOB',
                  'buggy':'TEXT',
                  'min_patch':'TEXT',
                  'first_patch':'TEXT',
                  'min_generation':'INTEGER',
                  'first_generation':'INTEGER',
                  'rps':'REAL'}
    foreign = 'FOREIGN KEY (run_id) REFERENCES run(id), FOREIGN KEY (instance_id) REFERENCES instance(id)'
    query, _query = make_query(cur, table, table_dict, foreign)
    _query['run_id'] = run_id

    total_rps = 0
    success = 0
    for instance_id, buggy in buggy_programs.items():
        is_sol = False
        min_patch = None
        first_patch = None
        min_gen = None
        first_gen = None
        rps = None
        buggy = regularize(buggy)
        if instance_id in patches.keys():
            first_gen, first_patch, min_gen, min_patch = patches[instance_id]
            rps = relative_patch_size(buggy, min_patch)
            is_sol = True
            total_rps += rps
            success += 1
        _query['instance_id'] = instance_id
        _query['solution'] = is_sol
        _query['buggy'] = buggy
        _query['min_patch'] = min_patch
        _query['first_patch'] = first_patch
        _query['min_generation'] = min_gen
        _query['first_generation'] = first_gen
        _query['rps'] = rps
        save_db(con, cur, query, _query)
    avg_rps = divide(total_rps,success)

    print(f'{len(patches)} Patches are generated.')
    print(f'Repair Rate: {round(success/len(buggy_programs), 2)*100}')
    print(f'AVG RPS: {avg_rps}')
    con.close()
