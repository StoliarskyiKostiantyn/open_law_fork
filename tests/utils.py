from app import models as m
from app.controllers.create_access_groups import (
    create_editor_group,
    create_moderator_group,
)

from random import randint

TEST_ADMIN_NAME = "bob"
TEST_ADMIN_EMAIL = "bob@test.com"
TEST_ADMIN_PASSWORD = "password"


def create(username=TEST_ADMIN_NAME, password=TEST_ADMIN_PASSWORD):
    user = m.User(username=username)
    user.password = password
    user.save()
    return user.id


def login(client, username=TEST_ADMIN_NAME, password=TEST_ADMIN_PASSWORD):
    user = m.User.query.filter_by(username=username).first()
    response = client.post(
        "/login", data=dict(user_id=username, password=password), follow_redirects=True
    )
    return response, user


def logout(client):
    return client.get("/logout", follow_redirects=True)


def create_test_book(owner_id: int, entity_id: int = randint(1, 100)):
    book: m.Book = m.Book(
        label=f"Book {entity_id}", about=f"About {entity_id}", user_id=owner_id
    ).save()

    version: m.BookVersion = m.BookVersion(semver="1.0.0", book_id=book.id).save()

    root_collection: m.Collection = m.Collection(
        label="Root", version_id=version.id, is_root=True
    ).save()

    collection: m.Collection = m.Collection(
        label=f"Collection {entity_id}",
        version_id=version.id,
        is_leaf=True,
        parent_id=root_collection.id,
    ).save()

    section: m.Section = m.Section(
        label=f"Section {entity_id}",
        user_id=owner_id,
        collection_id=collection.id,
        version_id=version.id,
    ).save()

    interpretation: m.Interpretation = m.Interpretation(
        section_id=section.id,
        text=f"Interpretation Text {entity_id}",
        user_id=owner_id,
    ).save()

    m.Comment(
        text=f"Comment {entity_id}",
        user_id=owner_id,
        interpretation_id=interpretation.id,
    ).save()

    # subcollection
    collection_2: m.Collection = m.Collection(
        label=f"Collection {entity_id}",
        version_id=version.id,
        parent_id=root_collection.id,
    ).save()

    subcollection: m.Collection = m.Collection(
        label=f"subCollection {entity_id}",
        version_id=version.id,
        parent_id=collection_2.id,
        is_leaf=True,
    ).save()

    # access groups
    editor_access_group = create_editor_group(book_id=book.id)
    moderator_access_group = create_moderator_group(book_id=book.id)
    access_groups = [editor_access_group, moderator_access_group]

    for access_group in access_groups:
        m.BookAccessGroups(book_id=book.id, access_group_id=access_group.id).save()
        # root
        m.CollectionAccessGroups(
            collection_id=root_collection.id, access_group_id=access_group.id
        ).save()
        # leaf
        m.CollectionAccessGroups(
            collection_id=collection.id, access_group_id=access_group.id
        ).save()

        m.CollectionAccessGroups(
            collection_id=collection_2.id, access_group_id=access_group.id
        ).save()
        # subcollection
        m.CollectionAccessGroups(
            collection_id=subcollection.id, access_group_id=access_group.id
        ).save()

    # -------------

    return book


def check_if_nested_book_entities_is_deleted(book: m.Book, is_deleted: bool = True):
    for version in book.versions:
        version: m.BookVersion
        assert version.is_deleted == is_deleted

        check_if_nested_version_entities_is_deleted(version)


def check_if_nested_version_entities_is_deleted(
    book_version: m.BookVersion, is_deleted: bool = True
):
    root_collection: m.Collection = book_version.root_collection
    assert root_collection.is_deleted == is_deleted
    for collection in root_collection.children:
        collection: m.Collection
        assert collection.is_deleted == is_deleted

        check_if_nested_collection_entities_is_deleted(collection)


def check_if_nested_collection_entities_is_deleted(
    collection: m.Collection, is_deleted: bool = True
):
    for section in collection.sections:
        section: m.Section
        assert section.is_deleted == is_deleted
        check_if_nested_section_entities_is_deleted(section, is_deleted)


def check_if_nested_section_entities_is_deleted(
    section: m.Section, is_deleted: bool = True
):
    for interpretation in section.interpretations:
        interpretation: m.Interpretation
        assert interpretation.is_deleted == is_deleted

        check_if_nested_interpretation_entities_is_deleted(interpretation, is_deleted)


def check_if_nested_interpretation_entities_is_deleted(
    interpretation: m.Interpretation, is_deleted: bool = True
):
    for comment in interpretation.comments:
        comment: m.Comment
        assert comment.is_deleted == is_deleted


def check_if_nested_comment_entities_is_deleted(
    comment: m.Comment, is_deleted: bool = True
):
    for child in comment.children:
        child: m.Comment
        assert child.is_deleted == is_deleted
