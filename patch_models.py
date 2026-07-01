with open('/app/models.py', 'r') as f:
    content = f.read()

# Add yearly_goal to User model
if 'yearly_goal' not in content:
    content = content.replace('is_admin = db.Column(db.Boolean, default=False) # NEW: Admin privilege flag', 
                              'is_admin = db.Column(db.Boolean, default=False) # NEW: Admin privilege flag\n    yearly_goal = db.Column(db.Integer, default=50) # NEW: Customizable yearly reading goal')

with open('/app/models.py', 'w') as f:
    f.write(content)
