import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.exceptions import HTTPException
from flask_migrate import Migrate
from flask_admin import Admin

from app.logger import log

# instantiate extensions
login_manager = LoginManager()
db = SQLAlchemy()
migration = Migrate()


def create_app(environment="development"):
    from config import config
    from app.views import (
        main_blueprint,
        auth_blueprint,
        user_blueprint,
        book_blueprint,
        home_blueprint,
        vote_blueprint,
        approve_blueprint,
        star_blueprint,
        search_blueprint,
    )
    from app import models as m

    # Instantiate app.
    app = Flask(__name__)

    # Set app config.
    env = os.environ.get("APP_ENV", environment)
    configuration = config(env)
    app.config.from_object(configuration)
    configuration.configure(app)
    log(log.INFO, "Configuration: [%s]", configuration.ENV)

    # Set up extensions.
    db.init_app(app)
    migration.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints.
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(book_blueprint)
    app.register_blueprint(home_blueprint)
    app.register_blueprint(vote_blueprint)
    app.register_blueprint(approve_blueprint)
    app.register_blueprint(star_blueprint)
    app.register_blueprint(search_blueprint)

    # Set up flask login.
    @login_manager.user_loader
    def get_user(id):
        return m.User.query.get(int(id))

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.anonymous_user = m.AnonymousUser

    # Jinja globals
    from app.controllers.jinja_globals import (
        form_hidden_tag,
        display_tags,
        build_qa_url_using_interpretation,
        recursive_render,
    )

    app.jinja_env.globals["form_hidden_tag"] = form_hidden_tag
    app.jinja_env.globals["display_tags"] = display_tags
    app.jinja_env.globals["build_qa_url"] = build_qa_url_using_interpretation
    app.jinja_env.globals["recursive_render"] = recursive_render

    # Error handlers.
    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        return render_template("error.html", error=exc), exc.code

    # flask admin
    from app.controllers.flask_admin_customization import (
        CustomAdminIndexView,
        ProtectedModelView,
    )

    app.config["FLASK_ADMIN_SWATCH"] = "Flatly"
    admin = Admin(
        app,
        name="Open Law Admin",
        template_mode="bootstrap3",
        index_view=CustomAdminIndexView(),
    )

    for view in [
        ProtectedModelView(m.User, db.session, name="User", endpoint="/user_"),
        ProtectedModelView(m.Book, db.session, name="Book", endpoint="/book_"),
        ProtectedModelView(
            m.Collection, db.session, name="Collection", endpoint="/collection_"
        ),
        ProtectedModelView(m.Section, db.session, name="Section", endpoint="/section_"),
        ProtectedModelView(
            m.Interpretation,
            db.session,
            name="Interpretation",
            endpoint="/interpretation_",
        ),
        ProtectedModelView(m.Comment, db.session, name="Comment", endpoint="/comment_"),
        ProtectedModelView(m.Tag, db.session, name="Tag", endpoint="/tag_"),
    ]:
        admin.add_view(view)

    return app
