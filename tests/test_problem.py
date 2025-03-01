import io
import pytest
from zipfile import ZipFile
from tests.base_tester import BaseTester
from mongo import *


def get_file(file):
    with open("./tests/problem_test_case/" + file, 'rb') as f:
        return {'case': (io.BytesIO(f.read()), "test_case.zip")}


def description_dict():
    return {
        'description': 'Test description.',
        'input': '',
        'output': '',
        'hint': '',
        'sampleInput': [],
        'sampleOutput': []
    }


class TestProblem(BaseTester):
    # add a problem which status value is invalid (POST /problem/manage)
    def test_add_with_invalid_value(self, client_admin):

        # create courses
        client_admin.post('/course',
                          json={
                              'course': 'math',
                              'teacher': 'admin'
                          })
        client_admin.post('/course',
                          json={
                              'course': 'English',
                              'teacher': 'admin'
                          })
        client_admin.put('/course/math',
                         json={
                             'TAs': ['admin'],
                             'studentNicknames': {
                                 'student': 'noobs'
                             }
                         })

        request_json_with_invalid_json = {
            'courses': ['math'],
            'status': 2,  # Invalid value
            'type': 0,
            'problemName': 'Test problem name',
            'description': description_dict(),
            'tags': [],
            'testCaseInfo': {
                'language':
                1,
                'fillInTemplate':
                '',
                'tasks': [{
                    'caseCount': 1,
                    'taskScore': 100,
                    'memoryLimit': 1000,
                    'timeLimit': 1000
                }]
            }
        }
        rv = client_admin.post('/problem/manage',
                               json=request_json_with_invalid_json)
        json = rv.get_json()
        assert rv.status_code == 400
        assert json['status'] == 'err'
        assert json['message'] == 'Invalid or missing arguments.'

    # add a problem which problem name is misssing (POST /problem/manage)
    def test_add_with_missing_argument(self, client_admin):
        request_json_with_missing_argument = {
            'courses': ['math'],
            'status': 1,
            'type': 0,
            #  'problem_name': 'Test problem name',	# missing argument
            'description': description_dict(),
            'tags': [],
            'testCaseInfo': {
                'language':
                1,
                'fillInTemplate':
                '',
                'tasks': [{
                    'caseCount': 1,
                    'taskScore': 100,
                    'memoryLimit': 1000,
                    'timeLimit': 1000
                }]
            }
        }
        rv = client_admin.post('/problem/manage',
                               json=request_json_with_missing_argument)
        json = rv.get_json()
        assert json['message'] == 'Invalid or missing arguments.'
        assert rv.status_code == 400
        assert json['status'] == 'err'

    # add a offline problem which problem_id = 1 (POST /problem/manage)
    def test_add_offline_problem(self, client_admin):
        request_json = {
            'courses': ['English'],
            'status': 1,
            'type': 0,
            'problemName': 'Offline problem',
            'description': description_dict(),
            'tags': [],
            'testCaseInfo': {
                'language':
                1,
                'fillInTemplate':
                '',
                'tasks': [{
                    'caseCount': 1,
                    'taskScore': 100,
                    'memoryLimit': 1000,
                    'timeLimit': 1000
                }]
            }
        }
        rv = client_admin.post('/problem/manage', json=request_json)
        json = rv.get_json()
        id = json['data']['problemId']

        rv = client_admin.put(f'/problem/manage/{id}',
                              data=get_file('default/test_case.zip'))
        json = rv.get_json()

        assert rv.status_code == 200, json
        assert json['status'] == 'ok'
        assert json['message'] == 'Success.'

    # add a online problem which problem_id = 2 (POST /problem/manage)
    def test_add_online_problem(self, client_admin):
        request_json = {
            'courses': ['math'],
            'status': 0,
            'type': 0,
            'problemName': 'Online problem',
            'description': description_dict(),
            'tags': [],
            'testCaseInfo': {
                'language':
                1,
                'fillInTemplate':
                '',
                'tasks': [{
                    'caseCount': 1,
                    'taskScore': 100,
                    'memoryLimit': 1000,
                    'timeLimit': 1000
                }]
            }
        }
        rv = client_admin.post('/problem/manage', json=request_json)
        json = rv.get_json()
        id = json['data']['problemId']

        rv = client_admin.put(f'/problem/manage/{id}',
                              data=get_file('default/test_case.zip'))
        json = rv.get_json()
        assert rv.status_code == 200
        assert json['status'] == 'ok'
        assert json['message'] == 'Success.'

    # admin get problem list (GET /problem)
    def test_admin_get_problem_list(self, client_admin):
        rv = client_admin.get('/problem?offset=0&count=5')
        json = rv.get_json()
        assert rv.status_code == 200
        assert json['status'] == 'ok'
        assert json['message'] == 'Success.'
        assert json['data'] == [{
            'problemId': 3,
            'type': 0,
            'problemName': 'Offline problem',
            'status': 1,
            'tags': [],
            'ACUser': 0,
            'submitter': 0,
            'quota': -1,
            'submitCount': 0
        }, {
            'problemId': 4,
            'type': 0,
            'problemName': 'Online problem',
            'status': 0,
            'tags': [],
            'ACUser': 0,
            'submitter': 0,
            'quota': -1,
            'submitCount': 0
        }]

    # admin get problem list with a filter(GET /problem)
    def test_admin_get_problem_list_with_filter(self, client_admin):
        rv = client_admin.get('/problem?offset=0&count=5&course=English')
        json = rv.get_json()
        assert rv.status_code == 200
        assert json['status'] == 'ok'
        assert json['message'] == 'Success.'
        assert json['data'] == [{
            'problemId': 3,
            'type': 0,
            'problemName': 'Offline problem',
            'status': 1,
            'tags': [],
            'ACUser': 0,
            'submitter': 0,
            'quota': -1,
            'submitCount': 0
        }]

    def test_admin_get_problem_list_with_unexist_params(self, client_admin):
        # unexisted course
        rv, rv_json, rv_data = self.request(
            client_admin,
            'get',
            '/problem?offset=0&count=-1&course=Programming',
        )
        assert rv.status_code == 200
        assert len(rv_data) == 0
        # unexisted tags
        rv, rv_json, rv_data = self.request(
            client_admin,
            'get',
            '/problem?offset=0&count=-1&tags=yo',
        )
        assert rv.status_code == 200
        assert len(rv_data) == 0

    # student get problem list (GET /problem)
    def test_student_get_problem_list(self, client_student):
        rv = client_student.get('/problem?offset=0&count=5')
        json = rv.get_json()
        assert rv.status_code == 200
        assert json['status'] == 'ok'
        assert json['message'] == 'Success.'
        assert json['data'] == [{
            'problemId': 4,
            'type': 0,
            'problemName': 'Online problem',
            'status': 0,
            'tags': [],
            'ACUser': 0,
            'submitter': 0,
            'quota': -1,
            'submitCount': 0
        }]

    # admin view offline problem (GET /problem/<problem_id>)
    def test_admin_view_offline_problem(self, client_admin):
        rv = client_admin.get('/problem/3')
        json = rv.get_json()
        assert rv.status_code == 200
        assert json['status'] == 'ok'
        assert json['message'] == 'Problem can view.'
        assert json['data'] == {
            'status':
            1,
            'type':
            0,
            'problemName':
            'Offline problem',
            'description':
            description_dict(),
            'owner':
            'admin',
            'tags': [],
            'courses': ['English'],
            'allowedLanguage':
            7,
            'testCase': [
                {
                    'caseCount': 1,
                    'memoryLimit': 1000,
                    'taskScore': 100,
                    'timeLimit': 1000,
                },
            ],
            'quota':
            -1,
            'submitCount':
            0,
            'defaultCode':
            '',
            'highScore':
            0,
        }

    # student view offline problem (GET /problem/<problem_id>)
    def test_student_view_offline_problem(self, client_student):
        rv = client_student.get('/problem/3')
        json = rv.get_json()
        assert rv.status_code == 403
        assert json['status'] == 'err'
        assert json['message'] == 'Problem cannot view.'

    # student view online problem (GET /problem/<problem_id>)
    def test_student_view_online_problem(self, client_student):
        rv = client_student.get('/problem/4')
        json = rv.get_json()
        assert rv.status_code == 200
        assert json['status'] == 'ok'
        assert json['message'] == 'Problem can view.'
        assert json['data'] == {
            'status':
            0,
            'type':
            0,
            'problemName':
            'Online problem',
            'description':
            description_dict(),
            'owner':
            'admin',
            'tags': [],
            'courses': ['math'],
            'allowedLanguage':
            7,
            'testCase': [
                {
                    'caseCount': 1,
                    'memoryLimit': 1000,
                    'taskScore': 100,
                    'timeLimit': 1000,
                },
            ],
            'quota':
            -1,
            'submitCount':
            0,
            'defaultCode':
            '',
            'highScore':
            0,
        }

    # student view problem not exist (GET /problem/<problem_id>)
    def test_student_view_problem_not_exist(self, client_student):
        rv = client_student.get('/problem/0')
        json = rv.get_json()
        assert rv.status_code == 404
        assert json['status'] == 'err'

    # student change the name of a problem (PUT /problem/manage/<problem_id>)
    def test_student_edit_problem(self, client_student):
        request_json = {
            'courses': [],
            'status': 1,
            'type': 0,
            'problemName': 'Offline problem (edit)',
            'description': description_dict(),
            'tags': [],
            'testCaseInfo': {
                'language':
                1,
                'fillInTemplate':
                '',
                'tasks': [{
                    'caseCount': 1,
                    'taskScore': 100,
                    'memoryLimit': 1000,
                    'timeLimit': 1000
                }]
            },
        }
        rv = client_student.put('/problem/manage/1', json=request_json)
        json = rv.get_json()
        assert rv.status_code == 403
        assert json['status'] == 'err'
        assert json['message'] == 'Insufficient Permissions'

    # non-owner teacher change the name of a problem (PUT /problem/manage/<problem_id>)
    def test_teacher_not_owner_edit_problem(self, client_teacher):
        request_json = {
            'courses': [],
            'status': 1,
            'type': 0,
            'problemName': 'Offline problem (edit)',
            'description': description_dict(),
            'tags': [],
            'testCaseInfo': {
                'language':
                1,
                'fillInTemplate':
                '',
                'tasks': [{
                    'caseCount': 1,
                    'taskScore': 100,
                    'memoryLimit': 1000,
                    'timeLimit': 1000
                }]
            }
        }
        rv = client_teacher.put('/problem/manage/1', json=request_json)
        json = rv.get_json()
        assert rv.status_code == 403
        assert json['status'] == 'err'
        assert json['message'] == 'Not the owner.'

    # admin change the name of a problem (PUT /problem/manage/<problem_id>)
    def test_admin_edit_problem_with_non_exist_course(self, client_admin):
        request_json = {
            'courses': ['PE'],
            'status': 1,
            'type': 0,
            'problemName': 'Offline problem (edit)',
            'description': description_dict(),
            'tags': [],
            'testCaseInfo': {
                'language':
                1,
                'fillInTemplate':
                '',
                'tasks': [{
                    'caseCount': 1,
                    'taskScore': 100,
                    'memoryLimit': 1000,
                    'timeLimit': 1000
                }]
            }
        }
        rv = client_admin.put('/problem/manage/1', json=request_json)
        json = rv.get_json()
        print(json)
        assert rv.status_code == 404

    # admin change the name of a problem (PUT /problem/manage/<problem_id>)
    def test_admin_edit_problem(self, client_admin):
        request_json = {
            'courses': [],
            'status': 1,
            'type': 0,
            'problemName': 'Offline problem (edit)',
            'description': description_dict(),
            'tags': [],
            'testCaseInfo': {
                'language':
                1,
                'fillInTemplate':
                '',
                'tasks': [{
                    'caseCount': 1,
                    'taskScore': 100,
                    'memoryLimit': 1000,
                    'timeLimit': 1000
                }]
            }
        }
        rv = client_admin.put('/problem/manage/3', json=request_json)
        json = rv.get_json()
        print(json)
        assert rv.status_code == 200
        assert json['status'] == 'ok'
        assert json['message'] == 'Success.'

    # admin get information of a problem (GET /problem/manage/<problem_id>)
    def test_admin_manage_problem(self, client_admin):
        rv = client_admin.get('/problem/manage/3')
        json = rv.get_json()
        assert rv.status_code == 200
        assert json['status'] == 'ok'
        assert json['message'] == 'Success.'
        assert json['data'] == {
            'courses': [],
            'status': 1,
            'type': 0,
            'problemName': 'Offline problem (edit)',
            'description': description_dict(),
            'tags': [],
            'testCase': {
                'language':
                1,
                'fillInTemplate':
                '',
                'tasks': [{
                    'caseCount': 1,
                    'taskScore': 100,
                    'memoryLimit': 1000,
                    'timeLimit': 1000
                }]
            },
            'ACUser': 0,
            'submitter': 0,
            'allowedLanguage': 7,
            'canViewStdout': True,
            'quota': -1,
            'submitCount': 0
        }

    def test_admin_update_problem_test_case(self, client_admin):
        # update test case
        rv, rv_json, rv_data = BaseTester.request(
            client_admin,
            'put',
            '/problem/manage/3',
            data=get_file('bogay/test_case.zip'),
        )
        assert rv.status_code == 200, rv_json
        # check content
        rv, rv_json, rv_data = BaseTester.request(
            client_admin,
            'get',
            '/problem/3/testcase',
        )
        assert rv.status_code == 200
        with ZipFile(io.BytesIO(rv.data)) as zf:
            ns = sorted(zf.namelist())
            in_ns = ns[::2]
            out_ns = ns[1::2]
            ns = zip(in_ns, out_ns)
            _io = [(
                zf.read(in_n),
                zf.read(out_n),
            ) for in_n, out_n in ns]
        assert _io == [(b'I AM A TEAPOT\n', b'I AM A TEAPOT\n')], rv_data

    def test_admin_update_problem_test_case_with_invalid_data(
        self,
        client_admin,
    ):
        # upload a test case with invalid data
        rv, rv_json, rv_data = BaseTester.request(
            client_admin,
            'put',
            '/problem/manage/1',
            data=get_file('task-exceed/test_case.zip'),
        )
        assert rv.status_code == 400

    # non-owner teacher get information of a problem (GET /problem/manage/<problem_id>)
    def test_teacher_not_owner_manage_problem(self, client_teacher):
        rv = client_teacher.get('/problem/manage/1')
        json = rv.get_json()
        assert rv.status_code == 403
        assert json['status'] == 'err'
        assert json['message'] == 'Not the owner.'

    # student get information of a problem (GET /problem/manage/<problem_id>)
    def test_student_manage_problem(self, client_student):
        rv = client_student.get('/problem/manage/1')
        json = rv.get_json()
        assert rv.status_code == 403
        assert json['status'] == 'err'
        assert json['message'] == 'Insufficient Permissions'

    # student delete problem (DELETE /problem/manage/<problem_id>)
    def test_student_delete_problem(self, client_student):
        rv = client_student.delete('/problem/manage/1')
        json = rv.get_json()
        assert rv.status_code == 403
        assert json['status'] == 'err'
        assert json['message'] == 'Insufficient Permissions'

    # non-owner teacher delete problem (DELETE /problem/manage/<problem_id>)
    def test_teacher_not_owner_delete_problem(self, client_teacher):
        rv = client_teacher.delete('/problem/manage/1')
        json = rv.get_json()
        assert rv.status_code == 403
        assert json['status'] == 'err'
        assert json['message'] == 'Not the owner.'

    # admin delete problem (DELETE /problem/manage/<problem_id>)
    def test_admin_delete_problem(self, client_admin):
        rv = client_admin.delete('/problem/manage/1')
        json = rv.get_json()
        assert rv.status_code == 200
        assert json['status'] == 'ok'
        assert json['message'] == 'Success.'

    def test_check_delete_successfully(self, client_admin):
        rv = client_admin.get('/problem/1')
        json = rv.get_json()
        assert rv.status_code == 404
        assert json['status'] == 'err'
