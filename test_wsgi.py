import base64
import json
import pytest

from collections import namedtuple
from unittest import mock

import wsgi

Response = namedtuple('Response', ['status_code'])


@pytest.fixture
def client():
    wsgi.application.config['TESTING'] = True

    with wsgi.application.test_client() as client:
        yield client


@pytest.fixture
def auth_headers():
    authstr = base64.b64encode(b'testuser:testpass').decode()
    headers = {
        'Authorization': f'Basic {authstr}',
    }

    return headers


@pytest.fixture
def mock_openshift():
    return mock.Mock()


@mock.patch('wsgi.open')
@mock.patch('wsgi.get_openshift')
def test_get_user_unauth(mock_get_openshift, mock_open, client):
    rv = client.get('/users/testuser')
    assert rv.status_code == 401


@mock.patch('wsgi.get_openshift')
def test_get_moc_user_true(mock_get_openshift, client, mock_openshift,
                           auth_headers):
    mock_openshift.user_exists.return_value = True
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.get('/users/testuser',
                        headers=auth_headers)

    assert rv.status_code == 200

    data = json.loads(rv.get_data())
    assert data['msg'] == "user (testuser) exists"


@mock.patch('wsgi.get_openshift')
def test_get_moc_user_false(mock_get_openshift, client, mock_openshift,
                            auth_headers):
    mock_openshift.user_exists.return_value = False
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.get('/users/testuser',
                        headers=auth_headers)

    assert rv.status_code == 400

    data = json.loads(rv.get_data())
    assert data['msg'] == "user (testuser) does not exist"


@mock.patch('wsgi.get_openshift')
def test_get_moc_rolebindings_false(mock_get_openshift, client, mock_openshift,
                                    auth_headers):
    mock_openshift.user_rolebinding_exists.return_value = False
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.get('/users/testuser/projects/testproject/roles/testrole',
                        headers=auth_headers)

    assert rv.status_code == 404

    data = json.loads(rv.get_data())
    assert data['msg'] == "user role does not exists (testproject,testuser,testrole)"


@mock.patch('wsgi.get_openshift')
def test_get_moc_rolebindings_true(mock_get_openshift, client, mock_openshift,
                                   auth_headers):
    mock_openshift.user_rolebinding_exists.return_value = True
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.get('/users/testuser/projects/testproject/roles/testrole',
                        headers=auth_headers)

    assert rv.status_code == 200

    data = json.loads(rv.get_data())
    assert data['msg'] == "user role exists (testproject,testuser,testrole)"


@mock.patch('wsgi.get_openshift')
def test_create_moc_rolebindings(mock_get_openshift, client, mock_openshift,
                                 auth_headers):
    mock_openshift.update_user_role_project.return_value = 'dummy response'
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.put('/users/testuser/projects/testproject/roles/testrole',
                        headers=auth_headers)

    assert rv.status_code == 200


@mock.patch('wsgi.get_openshift')
def test_delete_moc_rolebindings(mock_get_openshift, client, mock_openshift,
                                 auth_headers):
    mock_openshift.update_user_role_project.return_value = 'dummy response'
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.delete('/users/testuser/projects/testproject/roles/testrole',
                           headers=auth_headers)

    assert rv.status_code == 200


@mock.patch('wsgi.get_openshift')
def test_get_moc_project_false(mock_get_openshift, client, mock_openshift,
                               auth_headers):
    mock_openshift.project_exists.return_value = False
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.get('/projects/testproject',
                        headers=auth_headers)

    assert rv.status_code == 400

    data = json.loads(rv.get_data())
    assert data['msg'] == "project does not exist (testproject)"


@mock.patch('wsgi.get_openshift')
def test_get_moc_project_true(mock_get_openshift, client, mock_openshift,
                              auth_headers):
    mock_openshift.project_exists.return_value = True
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.get('/projects/testproject',
                        headers=auth_headers)

    assert rv.status_code == 200

    data = json.loads(rv.get_data())
    assert data['msg'] == "project exists (testproject)"


@mock.patch('wsgi.get_openshift')
def test_create_moc_project_bad_name(mock_get_openshift, client, mock_openshift,
                                     auth_headers):
    mock_openshift.cnvt_project_name.return_value = 'doesnotmatch'
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.put('/projects/testproject',
                        headers=auth_headers)

    assert rv.status_code == 400

    data = json.loads(rv.get_data())
    assert data['msg'] == "ERROR: project name must match regex '[a-z0-9]([-a-z0-9]*[a-z0-9])?'"


@mock.patch('wsgi.get_openshift')
def test_create_moc_project_conflict(mock_get_openshift, client, mock_openshift,
                                     auth_headers):
    mock_openshift.cnvt_project_name.return_value = 'testproject'
    mock_openshift.project_exists.return_value = True
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.put('/projects/testproject',
                        headers=auth_headers)

    assert rv.status_code == 400

    data = json.loads(rv.get_data())
    assert data['msg'] == "project currently exist (testproject)"


@mock.patch('wsgi.get_openshift')
def test_create_moc_project(mock_get_openshift, client, mock_openshift,
                            auth_headers):
    mock_openshift.cnvt_project_name.return_value = 'testproject'
    mock_openshift.project_exists.return_value = False
    mock_openshift.create_project.return_value = Response(200)
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.put('/projects/testproject',
                        headers=auth_headers,
                        json={'displayName': 'Test Project'})

    assert rv.status_code == 200

    data = json.loads(rv.get_data())
    assert data['msg'] == "project created (testproject)"


@mock.patch('wsgi.get_openshift')
def test_create_moc_project_fails(mock_get_openshift, client, mock_openshift,
                                  auth_headers):
    mock_openshift.cnvt_project_name.return_value = 'testproject'
    mock_openshift.project_exists.return_value = False
    mock_openshift.create_project.return_value = Response(500)
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.put('/projects/testproject',
                        headers=auth_headers)

    assert rv.status_code == 400

    data = json.loads(rv.get_data())
    assert data['msg'] == "project unabled to be created (testproject)"


@mock.patch('wsgi.get_openshift')
def test_delete_moc_project(mock_get_openshift, client, mock_openshift,
                            auth_headers):
    mock_openshift.project_exists.return_value = True
    mock_openshift.delete_project.return_value = Response(200)
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.delete('/projects/testproject',
                           headers=auth_headers)

    assert rv.status_code == 200

    data = json.loads(rv.get_data())
    assert data['msg'] == "project deleted (testproject)"


@mock.patch('wsgi.get_openshift')
def test_delete_moc_project_fails(mock_get_openshift, client, mock_openshift,
                                  auth_headers):
    mock_openshift.project_exists.return_value = True
    mock_openshift.delete_project.return_value = Response(500)
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.delete('/projects/testproject',
                           headers=auth_headers)

    assert rv.status_code == 400

    data = json.loads(rv.get_data())
    assert data['msg'] == "project unabled to be deleted (testproject)"


@mock.patch('wsgi.get_openshift')
def test_delete_moc_project_missing(mock_get_openshift, client, mock_openshift,
                                    auth_headers):
    mock_openshift.project_exists.return_value = False
    mock_openshift.delete_project.return_value = Response(200)
    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.delete('/projects/testproject',
                           headers=auth_headers)

    assert rv.status_code == 400

    data = json.loads(rv.get_data())
    assert data['msg'] == "unable to delete, project does not exist(testproject)"


@pytest.mark.parametrize(
    'user_exists,user_create_res,identity_exists,identity_create_res,mapping_exists,mapping_create_res,status_code,msg',
    [
        (False, 200, False, 200, False, 200, 200, 'user created (testuser)'),
        (False, 500, False, 200, False, 200, 400, 'unable to create openshift user (testuser) 1'),
        (True, 200, True, 200, True, 200, 200, 'user currently exists (testuser)'),
        (False, 200, False, 500, True, 200, 400, 'unable to create openshift identity (moc-sso)'),
        (False, 200, False, 200, False, 500, 400, 'unable to create openshift user identity mapping (testuser)'),
    ])
@mock.patch('wsgi.get_openshift')
def test_create_moc_user(mock_get_openshift, client, mock_openshift,
                         auth_headers,
                         user_exists, user_create_res,
                         identity_exists, identity_create_res,
                         mapping_exists, mapping_create_res,
                         status_code, msg):
    mock_openshift.user_exists.return_value = user_exists
    mock_openshift.create_user.return_value = Response(user_create_res)

    mock_openshift.identity_exists.return_value = identity_exists
    mock_openshift.create_identity.return_value = Response(identity_create_res)

    mock_openshift.useridentitymapping_exists.return_value = mapping_exists
    mock_openshift.create_useridentitymapping.return_value = Response(mapping_create_res)

    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.put('/users/testuser',
                        headers=auth_headers)

    assert rv.status_code == status_code

    data = json.loads(rv.get_data())
    assert data['msg'] == msg


@pytest.mark.parametrize(
    'user_exists,user_delete_res,identity_exists,identity_delete_res,status_code,msg',
    [
        (True, 200, True, 200, 200, 'user deleted (testuser)'),
        (True, 500, True, 200, 400, 'unable to delete User (testuser) 1'),
        (True, 200, True, 500, 400, 'unable to delete identity (sso_auth)'),
        (False, 200, False, 200, 200, 'user does not currently exist (testuser)'),
    ])
@mock.patch('wsgi.get_openshift')
def test_delete_moc_user(mock_get_openshift, client, mock_openshift,
                         auth_headers,
                         user_exists, user_delete_res,
                         identity_exists, identity_delete_res,
                         status_code, msg):
    mock_openshift.user_exists.return_value = user_exists
    mock_openshift.delete_user.return_value = Response(user_delete_res)

    mock_openshift.identity_exists.return_value = identity_exists
    mock_openshift.delete_identity.return_value = Response(identity_delete_res)

    mock_get_openshift.return_value = mock_openshift

    with mock.patch('wsgi.open', mock.mock_open(read_data='testuser testpass')):
        rv = client.delete('/users/testuser',
                           headers=auth_headers)

    assert rv.status_code == status_code

    data = json.loads(rv.get_data())
    assert data['msg'] == msg


@pytest.mark.parametrize(
    'openshift_version', ['3', '4'],
)
def test_get_openshift(openshift_version):
    v3api = mock.Mock()
    v4api = mock.Mock()

    versions = {
        '3': v3api,
        '4': v4api,
    }

    env = {
        'OPENSHIFT_VERSION': openshift_version,
        'OPENSHIFT_URL': 'openshift',
    }

    v3api.return_value = v3api
    v4api.return_value = v4api

    with mock.patch('wsgi.openshift_3_x', v3api):
        with mock.patch('wsgi.openshift_4_x', v4api):
            with mock.patch('wsgi.os.environ', env):
                with mock.patch('wsgi.open', mock.mock_open(read_data='token')):
                    res = wsgi.get_openshift()

    assert res is versions[openshift_version]
