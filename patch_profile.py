with open('/app/templates/profile.html', 'r') as f:
    content = f.read()

# Add goal update form to profile page
form_html = """
        <div class="glass-card p-4 mb-5">
            <h4 class="mb-4"><i class="fas fa-bullseye text-primary me-2"></i> Reading Goal</h4>
            <form action="{{ url_for('update_goal') }}" method="POST" class="d-flex align-items-center">
                <label for="yearly_goal" class="me-3 fw-bold">Books per year:</label>
                <input type="number" class="form-control me-3" id="yearly_goal" name="yearly_goal" value="{{ current_user.yearly_goal }}" min="1" style="width: 120px;">
                <button type="submit" class="btn btn-primary hover-lift"><i class="fas fa-save me-2"></i> Update Goal</button>
            </form>
        </div>
"""

if 'Reading Goal' not in content:
    content = content.replace('<div class="glass-card p-4 mb-5">', f'{form_html}\n        <div class="glass-card p-4 mb-5">')

with open('/app/templates/profile.html', 'w') as f:
    f.write(content)
