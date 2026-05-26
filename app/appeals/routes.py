from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.appeals import bp
from app.appeals.forms import AppealForm
from app import db
from app.models import Appeal

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = AppealForm()
    if form.validate_on_submit():
        appeal = Appeal(
            user_id=current_user.id,
            plot_id=current_user.plot.id if current_user.plot else None,
            subject=form.subject.data,
            body=form.body.data
        )
        db.session.add(appeal)
        db.session.commit()
        flash('Ваше обращение принято. Номер обращения: {}'.format(appeal.id))
        return redirect(url_for('dashboard.home'))
    return render_template('appeals/create.html', title='Подать обращение', form=form)

@bp.route('/my')
@login_required
def my_appeals():
    appeals = Appeal.query.filter_by(user_id=current_user.id)\
                .order_by(Appeal.created_at.desc()).all()
    return render_template('appeals/my.html', title='Мои обращения', appeals=appeals)