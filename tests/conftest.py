from typing import Dict, List
from flask import Flask
from mongo import *
from mongo import engine
import mongomock.gridfs

import pytest
import random
from datetime import datetime
from zipfile import ZipFile
from collections import defaultdict
from tests.base_tester import random_string
from tests.test_homework import CourseData
from tests.test_problem import get_file


@pytest.fixture
def app(tmp_path):
    from app import app as flask_app
    app = flask_app()
    app.config['TESTING'] = True
    mongomock.gridfs.enable_gridfs_integration()
    # modify submission config for testing
    # use tmp dir to save user source code
    submission_tmp_dir = (tmp_path / Submission.config().TMP_DIR).absolute()
    submission_tmp_dir.mkdir(exist_ok=True)
    Submission.config().TMP_DIR = submission_tmp_dir
    return app


# TODO: share client may cause auth problem
@pytest.fixture
def client(app: Flask):
    return app.test_client()


@pytest.fixture
def forge_client(client):
    def seted_cookie(username):
        client.set_cookie('test.test', 'piann', User(username).secret)
        return client

    return seted_cookie


@pytest.fixture
def client_admin(forge_client):
    return forge_client('admin')


@pytest.fixture
def client_teacher(forge_client):
    return forge_client('teacher')


@pytest.fixture
def client_student(forge_client):
    return forge_client('student')


@pytest.fixture
def test_token():
    # Token for user: test
    return User('test').secret


@pytest.fixture
def test2_token():
    # Token for user: test2
    return User('test2').secret


def random_problem_data(username=None, status=-1, type=0, quota=-1):
    '''
    generate dummy problem data

    Args:
        username: problem owner's name, if not None, add this problem to his/her course
        status: problem status, if -1, random select from {0, 1}
    '''
    s = random_string()
    return {
        'courses':
        [engine.Course.objects.filter(
            teacher=username)[0].course_name] if username else [],
        'status':
        random.randint(0, 1) if status == -1 else status,
        'type':
        type,
        'description': {
            'description': '',
            'input': '',
            'output': '',
            'hint': '',
            'sample_input': [],
            'sample_output': []
        },
        'tags': ['test'],
        'problem_name':
        f'prob {s}',
        'test_case_info': {
            'language':
            2,
            'fill_in_template':
            '',
            'tasks': [
                {
                    'case_count': 1,
                    'task_score': 100,
                    'memory_limit': 32768,
                    'time_limit': 1000,
                },
            ],
        },
        'quota':
        quota,
    }


@pytest.fixture
def make_course(forge_client):
    def make_course(username, students={}, tas=[]):
        '''
        insert a dummy course data into DB

        Args:
            username -> str: course teacher's user name
            students -> dict[str, str]:
                course students, key is student's username and value is student's nickname
            tas -> list[str]:
                a list contains tas' username

        Return:
            generated course data
        '''
        # login with user name
        client = forge_client(username)
        # generate random dummy data
        c_data = CourseData(
            name=random_string(),
            teacher=username,
            students=students,
            tas=tas,
        )
        # add course
        assert Course.add_course(
            c_data.name,
            c_data.teacher,
        ) == True, f'course name: {c_data.name}\nteacher: {c_data.teacher}\n'
        # add students and TA
        rv = client.put(
            f'/course/{c_data.name}',
            json={
                'TAs': c_data.tas,
                'studentNicknames': c_data.students
            },
        )
        assert rv.status_code == 200, rv.get_json()

        client.cookie_jar.clear()
        return c_data

    return make_course


@pytest.fixture()
def problem_ids(forge_client):
    def problem_ids(
        username,
        length,
        add_to_course=False,
        status=0,
        type=0,
        quota=-1,
    ):
        '''
        insert dummy problems into db

        Args:
            - username: the problem owner's username
            - length: how many problem you want to create
        Return:
            a list of problem id that you create
        '''
        client = forge_client(username)
        rets = []  # created problem ids
        for _ in range(length):
            _id = Problem.add(
                **random_problem_data(
                    username=username if add_to_course else None,
                    status=status,
                    type=type,
                    quota=quota,
                ),
                **{'user': User(username)},
            )
            if Problem(_id).problem_type != 2:
                rv = client.put(
                    f'/problem/manage/{_id}',
                    data=get_file('default/test_case.zip'),
                )
                assert rv.status_code == 200, rv.get_json()
            rets.append(_id)
        # don't leave cookies!
        client.cookie_jar.clear()

        return rets

    return problem_ids


@pytest.fixture
def save_source(tmp_path):
    def save_source(filename, source, lang, ext=None):
        '''
        save user source codes to tmp dir
        currently only support one file.

        Args:
            filename: the source code's filename without extension
            source: source code (must be bytes-like object)
            lang: programming language, only accept {0, 1, 2}
            ext: main script extension want to use, if None, decided by lang

        Returns:
            a zip file contains source code
        '''
        # decide extension
        if not ext:
            ext = ['.c', '.cpp', '.py', '.pdf'][lang]
        # set path
        name = tmp_path / (filename + ext)
        zip_path = tmp_path / f'{name}.zip'
        # duplicated file
        if name.exists():
            raise FileExistsError(name)
        with open(name, 'wb') as f:
            f.write(source)
        with ZipFile(zip_path, 'w') as f:
            f.write(name, arcname=f'main{ext}')
        return True

    return save_source


@pytest.fixture
def get_source(tmp_path):
    def get_source(filename):
        '''
        get users zipped source by filename

        Args:
            filename: a string denote the source code's filename include extension

        Returns:
            the zip file
        '''
        path = tmp_path / f'{filename}.zip'

        if not path.exists():
            raise FileNotFoundError(path)

        return open(path, 'rb')

    return get_source


@pytest.fixture
def submit_once(app, get_source):
    def submit_once(name, pid, filename, lang, client=None):
        '''
        create one submission
        Args:
            name: user's name who want to create a submission
            pid: the problem id
            filename: source code's zip filename
            lang: language ID
        '''
        with app.app_context():
            now = datetime.now()
            try:
                submission = Submission.add(
                    problem_id=pid,
                    username=name,
                    lang=lang,
                    timestamp=now,
                )
            except engine.DoesNotExist as e:
                assert False, str(e)
            res = submission.submit(get_source(filename))
            assert res == True
        return submission.id

    return submit_once


@pytest.fixture
def submit(submit_once):
    def submit(
        names,
        pids,
        count,
        filename='base.c',
        lang=0,
    ) -> Dict[str, List[Submission]]:
        n2p = defaultdict(list)  # name to pid
        for n, p, _ in zip(names, pids, 'x' * count):
            n2p[n].append(p)
        n2s = defaultdict(list)  # name to submission id
        for name, ps in n2p.items():
            for p in ps:
                n2s[name].append(
                    submit_once(
                        name=name,
                        pid=p,
                        filename=filename,
                        lang=lang,
                    ))

        return n2s

    return submit
