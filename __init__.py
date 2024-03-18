import os
from flask import Flask
from flask import render_template

def create_app(test_config=None):
    
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )
    
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # apply the blueprints to the app
    from flaskr import auth, admin, student, supervisor, convenor, chair

    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(student.bp)
    app.register_blueprint(supervisor.bp)
    app.register_blueprint(convenor.bp)
    app.register_blueprint(chair.bp)
    
    app.secret_key = "super secret key"
    
    @app.route('/')
    def homepage():
        return render_template('homepage.html', title='Home')
    
    return app

