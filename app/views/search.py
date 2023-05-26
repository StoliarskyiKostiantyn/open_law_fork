from flask import Blueprint, render_template, request, jsonify, url_for
from sqlalchemy import func, and_, or_

from app import models as m, db
from app.controllers import create_pagination
from app.controllers.build_qa_url_using_interpretation import (
    build_qa_url_using_interpretation,
)
from app.logger import log


bp = Blueprint("search", __name__)


@bp.route("/search_interpretations", methods=["GET"])
def search_interpretations():
    q = request.args.get("q", type=str, default="").lower()
    interpretations = m.Interpretation.query.order_by(m.Interpretation.id).filter(
        (func.lower(m.Interpretation.plain_text).like(f"%{q}%"))
    )
    count = interpretations.count()
    pagination = create_pagination(total=interpretations.count())

    return render_template(
        "searchResultsInterpretations.html",
        query=q,
        interpretations=interpretations.paginate(
            page=pagination.page, per_page=pagination.per_page
        ),
        page=pagination,
        count=count,
    )


@bp.route("/search_books", methods=["GET"])
def search_books():
    q = request.args.get("q", type=str, default="")
    log(log.INFO, "Starting to build query for books")

    books = (
        m.Book.query.join(m.BookVersion, m.BookVersion.book_id == m.Book.id)
        .join(m.Collection, m.BookVersion.id == m.Collection.version_id, full=True)
        .join(m.Section, m.BookVersion.id == m.Section.version_id, full=True)
        .join(m.Interpretation, m.Interpretation.section_id == m.Section.id, full=True)
        .filter(
            or_(
                and_(
                    func.lower(m.Book.label).like(f"%{q}%"),
                ),
                and_(
                    func.lower(m.Collection.label).like(f"%{q}%"),
                    m.Collection.is_deleted == False,  # noqa: E712
                    m.Collection.is_root == False,  # noqa: E712
                ),
                and_(
                    func.lower(m.Section.label).like(f"%{q}%"),
                    m.Section.is_deleted == False,  # noqa: E712
                ),
                and_(
                    func.lower(m.Interpretation.plain_text).like(f"%{q}%"),
                    m.Interpretation.is_deleted == False,  # noqa: E712
                    m.Section.is_deleted == False,  # noqa: E712
                ),
            ),
            m.Book.is_deleted == False,  # noqa: E712
        )
        .group_by(m.Book.id)
    )

    log(log.INFO, "Get count of books")
    count = books.count()
    log(log.INFO, "Creating pagination")
    pagination = create_pagination(total=books.count())
    log(log.INFO, "Returning data to front")

    return render_template(
        "searchResultsBooks.html",
        query=q,
        books=books.paginate(page=pagination.page, per_page=pagination.per_page),
        page=pagination,
        count=count,
    )


@bp.route("/search_users", methods=["GET"])
def search_users():
    q = request.args.get("q", type=str, default="")
    users = (
        m.User.query.order_by(m.User.id)
        .filter(
            or_(
                func.lower(m.User.username).like(f"%{q}%"),
                func.lower(m.User.wallet_id).like(f"%{q}%"),
            )
        )
        .order_by(m.User.id.asc())
        .group_by(m.User.id)
    )

    count = users.count()
    pagination = create_pagination(total=users.count())

    return render_template(
        "searchResultsUsers.html",
        query=q,
        users=users.paginate(page=pagination.page, per_page=pagination.per_page),
        page=pagination,
        count=count,
    )


@bp.route("/search_tags", methods=["GET"])
def search_tags():
    q = request.args.get("q", type=str, default="")
    tags = m.Tag.query.order_by(m.Tag.id).filter(func.lower(m.Tag.name).like(f"%{q}%"))
    count = tags.count()
    pagination = create_pagination(total=tags.count())

    return render_template(
        "searchResultsTags.html",
        query=q,
        tags=tags.paginate(page=pagination.page, per_page=pagination.per_page),
        page=pagination,
        count=count,
    )


@bp.route("/tag_search_interpretations", methods=["GET"])
def tag_search_interpretations():
    tag_name = request.args.get("tag_name", type=str, default="")
    interpretations = (
        db.session.query(m.Interpretation)
        .filter(
            and_(
                func.lower(m.Tag.name) == (tag_name),
                m.InterpretationTag.tag_id == m.Tag.id,
                m.Interpretation.id == m.InterpretationTag.interpretation_id,
                m.Interpretation.is_deleted == False,  # noqa: E712
            )
        )
        .order_by(m.Interpretation.created_at.asc())
        .group_by(m.Interpretation.id)
    )

    pagination = create_pagination(total=interpretations.count())

    return render_template(
        "tagSearchResultsInterpretations.html",
        tag_name=tag_name,
        interpretations=interpretations.paginate(
            page=pagination.page, per_page=pagination.per_page
        ),
        page=pagination,
        count=interpretations.count(),
    )


@bp.route("/tag_search_books", methods=["GET"])
def tag_search_books():
    tag_name = request.args.get("tag_name", type=str, default="").lower()
    books = (
        db.session.query(m.Book)
        .filter(
            and_(
                func.lower(m.Tag.name) == (tag_name),
                m.BookTags.tag_id == m.Tag.id,
                m.Book.id == m.BookTags.book_id,
                m.Book.is_deleted == False,  # noqa: E712
            )
        )
        .order_by(m.Book.created_at.asc())
        .group_by(m.Book.id)
    )

    pagination = create_pagination(total=books.count())

    return render_template(
        "tagSearchResultsBooks.html",
        tag_name=tag_name,
        books=books.paginate(page=pagination.page, per_page=pagination.per_page),
        page=pagination,
        count=books.count(),
    )


@bp.route("/quick_search", methods=["GET"])
def quick_search():
    search_query = request.args.get("search_query", type=str, default="")
    interpretations = (
        m.Interpretation.query.order_by(m.Interpretation.id)
        .filter((func.lower(m.Interpretation.plain_text).like(f"%{search_query}%")))
        .limit(2)
    )
    interpretations_res = []
    for interpretation in interpretations:
        url_for_interpretation = build_qa_url_using_interpretation(interpretation)
        interpretations_res.append(
            {"label": interpretation.section.label, "url": url_for_interpretation}
        )
    books = (
        m.Book.query.order_by(m.Book.id)
        .filter((func.lower(m.Book.label).like(f"%{search_query}%")))
        .limit(2)
    )
    books_res = []
    for book in books:
        url_for_book = url_for("book.collection_view", book_id=book.id)
        books_res.append({"label": book.label, "url": url_for_book})

    users = (
        m.User.query.order_by(m.User.id)
        .filter(
            or_(
                func.lower(m.User.username).like(f"%{search_query}%"),
                func.lower(m.User.wallet_id).like(f"%{search_query}%"),
            )
        )
        .order_by(m.User.id.asc())
        .group_by(m.User.id)
        .limit(2)
    )
    users_res = []
    for user in users:
        url_for_user = url_for("user.profile", user_id=user.id)
        users_res.append({"label": user.username, "url": url_for_user})

    tags = (
        m.Tag.query.order_by(m.Tag.id)
        .filter(func.lower(m.Tag.name).like(f"%{search_query}%"))
        .limit(2)
    )
    tags_res = []
    for tag in tags:
        url_for_tag = url_for("search.tag_search_interpretations", tag_name=tag.name)
        tags_res.append({"label": tag.name, "url": url_for_tag})

    return jsonify(
        {
            "interpretations": interpretations_res,
            "books": books_res,
            "users": users_res,
            "tags": tags_res,
        }
    )
