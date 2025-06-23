sudo bash -c '
  echo "🔄 Pulling latest code..."

  # Mark the directory as safe for Git
  git config --global --add safe.directory /home/dev-gpu/nyx-campaign-agent

  # Change directory
  cd /home/dev-gpu/nyx-campaign-agent

  # Fix ownership (if needed)
  chown -R root:root /home/dev-gpu/nyx-campaign-agent

  # Set GitHub remote
  git remote set-url origin https://'"$GH_PERSONAL_ACCESS_TOKEN"'@github.com/tech-nyx/nyx-campaign-agent.git

  # Pull the latest changes
  git pull origin dev

  uv sync
  
  source .venv/bin/activate

  uv pip install -r requirements.txt


  #Restart or start
  nohup python3 main.py > campaign_agent.log 2>&1 &


  

  echo "✅ Deployment complete!"
'
