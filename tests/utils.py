from app.models import User

TEST_ADMIN_NAME = "bob"
TEST_ADMIN_EMAIL = "bob@test.com"
TEST_ADMIN_PASSWORD = "password"


def create(username=TEST_ADMIN_NAME, password=TEST_ADMIN_PASSWORD):
    user = User(username=username)
    user.password = password
    user.save()
    return user.id


def login(client, username=TEST_ADMIN_NAME, password=TEST_ADMIN_PASSWORD):
    user = User.query.filter_by(username=username).first()
    response = client.post(
        "/login", data=dict(user_id=username, password=password), follow_redirects=True
    )
    return response, user


def logout(client):
    return client.get("/logout", follow_redirects=True)