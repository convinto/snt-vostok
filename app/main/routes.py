from flask import render_template
from app.main import bp
from app.models import Post, Task

@bp.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    tasks = Task.query.order_by(Task.updated_at.desc()).all()
    return render_template('index.html', title='Главная', posts=posts, tasks=tasks)

@bp.route('/rekvizity')
def rekvizity():
    return render_template('rekvizity.html', title='Реквизиты')