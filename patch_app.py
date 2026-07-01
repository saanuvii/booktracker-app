with open('/app/app.py', 'r') as f:
    content = f.read()

# Replace hardcoded yearly goal
content = content.replace('yearly_goal = 50', 'yearly_goal = current_user.yearly_goal')

with open('/app/app.py', 'w') as f:
    f.write(content)
