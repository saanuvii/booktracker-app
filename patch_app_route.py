with open('/app/app.py', 'r') as f:
    content = f.read()

route_html = """
@app.route('/update_goal', methods=['POST'])
@login_required
def update_goal():
    try:
        new_goal = int(request.form.get('yearly_goal', 50))
        if new_goal < 1:
            new_goal = 1
        current_user.yearly_goal = new_goal
        db.session.commit()
        flash('Reading goal updated successfully!', 'success')
    except ValueError:
        flash('Invalid goal number.', 'danger')
    return redirect(url_for('profile'))

"""

if 'def update_goal' not in content:
    content = content.replace('@app.route(\'/profile\')', f'{route_html}@app.route(\'/profile\')')

with open('/app/app.py', 'w') as f:
    f.write(content)
