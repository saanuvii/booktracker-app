with open('/app/templates/profile.html', 'r') as f:
    content = f.read()

# Add goal update form to profile page
form_html = """
    <div class="col-md-12 mb-4">
        <div class="glass-panel p-4">
            <h4 class="mb-4">Reading Goal</h4>
            <form action="{{ url_for('update_goal') }}" method="POST" class="d-flex align-items-center">
                <label for="yearly_goal" class="me-3">Books per year:</label>
                <input type="number" class="form-control me-3" id="yearly_goal" name="yearly_goal" value="{{ current_user.yearly_goal }}" min="1" style="width: 100px; background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2);">
                <button type="submit" class="btn btn-primary">Update Goal</button>
            </form>
        </div>
    </div>
"""

if 'Reading Goal' not in content:
    content = content.replace('<div class="row">', f'<div class="row">\n{form_html}')

with open('/app/templates/profile.html', 'w') as f:
    f.write(content)
