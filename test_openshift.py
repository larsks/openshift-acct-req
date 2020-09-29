import json
import pytest

from unittest import mock

import openshift

test_token = 'secret'
test_url = 'example.com'
test_user = 'testuser'
test_project = 'testproject'


@pytest.fixture(autouse=True)
def mock_requests():
    openshift.requests = mock.Mock()


@pytest.fixture()
def api():
    mock_logger = mock.Mock()
    shift = openshift.openshift(test_url, test_token, mock_logger)
    return shift


@pytest.fixture()
def apiv3():
    mock_logger = mock.Mock()
    shift = openshift.openshift_3_x(test_url, test_token, mock_logger)
    return shift


@pytest.fixture()
def apiv4():
    mock_logger = mock.Mock()
    shift = openshift.openshift_4_x(test_url, test_token, mock_logger)
    return shift


@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_init(api):
    assert api.get_url() == test_url


@pytest.mark.parametrize('orig,modified', [
    ('test project', 'test-project'),
    (' test project', 'test-project'),
    ('test project ', 'test-project'),
    ('-test project', 'test-project'),
    ('test project-', 'test-project'),
    ('test-project', 'test-project'),
])
def test_cnvt_project_name(api, orig, modified):
    rv = api.cnvt_project_name(orig)
    assert rv == modified


@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_get_rolebindings(api):
    data = {
        'userNames': [
            test_user
        ]
    }

    expected_text = json.dumps(data)

    openshift.requests.get.return_value = mock.Mock(
        status_code=200,
        text=expected_text,
    )
    openshift.requests.get.return_value.json.return_value = data

    rv = api.get_rolebindings(test_project, 'admin')
    assert rv.status_code == 200
    assert rv.text == expected_text


@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_user_rolebinding_exists_true_v3(api):
    data = {
        'userNames': [
            test_user
        ]
    }

    expected_text = json.dumps(data)

    openshift.requests.get.return_value = mock.Mock(
        status_code=200,
        text=expected_text,
    )
    openshift.requests.get.return_value.json.return_value = data

    rv = api.user_rolebinding_exists(test_user, test_project, 'admin')
    assert rv


@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_user_rolebinding_exists_false_v3(api):
    data = {
        'userNames': [
        ]
    }

    expected_text = json.dumps(data)

    openshift.requests.get.return_value = mock.Mock(
        status_code=200,
        text=expected_text,
    )
    openshift.requests.get.return_value.json.return_value = data

    rv = api.user_rolebinding_exists(test_user, test_project, 'admin')
    assert not rv


@pytest.mark.parametrize('user,roles',
                         [
                             ('user1', ['admin', 'reader']),
                             ('user2', ['member', 'reader']),
                         ])
@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_get_all_moc_rolebindings(api, user, roles):
    data = {
        'admin': {
            'userNames': [
                'user1',
            ]
        },
        'edit': {
            'userNames': [
                'user2',
            ]
        },
        'view': {
            'userNames': [
                'user1',
                'user2',
            ]
        },
    }

    def _get(url, headers=None, verify=None):
        path = url.split('/')
        if path[-2] == 'rolebindings':
            rv = mock.Mock(
                status_code=200,
                text=json.dumps(data[path[-1]]),
            )
            rv.json.return_value = data[path[-1]]

            return rv

    openshift.requests.get.side_effect = _get
    rv = api.get_all_moc_rolebindings(user, test_project)

    assert rv.status_code == 200

    res = json.loads(rv.get_data())
    assert res['rolebindings'] == roles


@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_get_all_moc_rolebindings_none(api):
    data = {
        'userNames': [
        ]
    }

    expected_text = json.dumps(data)

    openshift.requests.get.return_value = mock.Mock(
        status_code=200,
        text=expected_text,
    )
    openshift.requests.get.return_value.json.return_value = data

    rv = api.get_all_moc_rolebindings(test_user, test_project)

    assert rv.status_code == 404

    res = json.loads(rv.get_data())
    assert 'rolebindings' not in res


@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_update_user_role_project_invalid_op(api):
    rv = api.update_user_role_project(test_project, test_user, 'admin', 'foo')
    assert rv.status_code == 400


@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_update_user_role_project_invalid_role(api):
    rv = api.update_user_role_project(test_project, test_user, 'foo', 'add')
    assert rv.status_code == 400


@pytest.mark.parametrize('role', ['admin', 'member', 'reader'])
@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_update_user_role_project_missing_success(api, role):
    openshift.requests.get.return_value = mock.Mock(
        status_code=404,
        text = 'dummy text',
    )

    with mock.patch('openshift.openshift_3_x.create_rolebindings'):
        with mock.patch('openshift.openshift_4_x.create_rolebindings'):
            ret = mock.Mock(
                status_code=200,
                text='dummy text',
            )
            openshift.openshift_3_x.create_rolebindings.return_value = ret
            openshift.openshift_4_x.create_rolebindings.return_value = ret

            rv = api.update_user_role_project(test_project, test_user, role, 'add')
            assert rv.status_code == 200
            data = json.loads(rv.get_data())
            assert data['msg'] == f'rolebinding created ({test_user},{test_project},{role})'


@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_update_user_role_project_add_missing_failure(api):
    openshift.requests.get.return_value = mock.Mock(
        status_code=404,
        text='dummy text',
    )

    with mock.patch('openshift.openshift_3_x.create_rolebindings'):
        with mock.patch('openshift.openshift_4_x.create_rolebindings'):
            ret = mock.Mock(
                status_code=400,
                text='dummy text',
            )
            openshift.openshift_3_x.create_rolebindings.return_value = ret
            openshift.openshift_4_x.create_rolebindings.return_value = ret

            rv = api.update_user_role_project(test_project, test_user, 'admin', 'add')
            assert rv.status_code == 400
            assert 'unable to create rolebinding' in json.loads(rv.get_data())['msg']


@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_update_user_role_project_add_exists_success_has_binding(api):
    openshift.requests.get.return_value = mock.Mock(
        status_code=200,
        text='dummy text',
    )

    openshift.requests.get.return_value.json.return_value = {
        'userNames': [test_user],
    }

    with mock.patch('openshift.openshift_3_x.create_rolebindings'):
        with mock.patch('openshift.openshift_4_x.create_rolebindings'):
            ret = mock.Mock(
                status_code=200,
                text='dummy text',
            )
            openshift.openshift_3_x.create_rolebindings.return_value = ret
            openshift.openshift_4_x.create_rolebindings.return_value = ret

            rv = api.update_user_role_project(test_project, test_user, 'member', 'add')
            assert rv.status_code == 400
            data = json.loads(rv.get_data())
            assert data['msg'] == f'rolebinding already exists - unable to add ({test_user},{test_project},member)'


@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_update_user_role_project_add_exists_success_no_binding(api):
    openshift.requests.get.return_value = mock.Mock(
        status_code=200,
        text='dummy text',
    )

    openshift.requests.get.return_value.json.return_value = {
        'userNames': [],
        'metadata': {},
    }

    openshift.requests.put.return_value = mock.Mock(
        status_code=200,
        text='dummy text',
    )

    with mock.patch('openshift.openshift_3_x.create_rolebindings'):
        with mock.patch('openshift.openshift_4_x.create_rolebindings'):
            ret = mock.Mock(
                status_code=200,
                text='dummy text',
            )
            openshift.openshift_3_x.create_rolebindings.return_value = ret
            openshift.openshift_4_x.create_rolebindings.return_value = ret

            rv = api.update_user_role_project(test_project, test_user, 'member', 'add')

            assert rv.status_code == 200
            data = json.loads(rv.get_data())
            assert data['msg'] == f'Added role to user on project'


@pytest.mark.parametrize('api', [
    pytest.lazy_fixture('apiv3'),
    pytest.lazy_fixture('apiv4')
])
def test_update_user_role_project_add_exists_success_no_binding_fails(api):
    openshift.requests.get.return_value = mock.Mock(
        status_code=200,
        text='dummy text',
    )

    openshift.requests.get.return_value.json.return_value = {
        'userNames': [],
        'metadata': {},
    }

    openshift.requests.put.return_value = mock.Mock(
        status_code=400,
        text='dummy text',
    )

    with mock.patch('openshift.openshift_3_x.create_rolebindings'):
        with mock.patch('openshift.openshift_4_x.create_rolebindings'):
            ret = mock.Mock(
                status_code=200,
                text='dummy text',
            )
            openshift.openshift_3_x.create_rolebindings.return_value = ret
            openshift.openshift_4_x.create_rolebindings.return_value = ret

            rv = api.update_user_role_project(test_project, test_user, 'member', 'add')

            assert rv.status_code == 400
            data = json.loads(rv.get_data())
            assert data['msg'] == f'unable to add role to user on project'
