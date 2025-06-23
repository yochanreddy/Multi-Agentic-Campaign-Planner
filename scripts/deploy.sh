sudo bash -c '
  echo "🔄 Pulling latest code..."   # Deployment start message

  # Mark the directory as safe for Git (to avoid permission warnings)
  git config --global --add safe.directory /home/dev-gpu/nyx-campaign-agent

  # Change directory to the campaign agent project folder
  cd /home/dev-gpu/nyx-campaign-agent

  # Fix ownership of the project directory (change to root user and group)
  chown -R root:root /home/dev-gpu/nyx-campaign-agent

  # Update Git remote URL to use the personal access token for authentication
  git remote set-url origin https://'"$GH_PERSONAL_ACCESS_TOKEN"'@github.com/tech-nyx/nyx-campaign-agent.git

  # Pull the latest code changes from the 'dev' branch
  git pull origin dev

  # Sync virtual environment or dependencies (assuming 'uv sync' is a custom command)
  uv sync

  # Activate the Python virtual environment
  source .venv/bin/activate

  # Install Python dependencies from requirements.txt inside the virtual environment
  uv pip install -r requirements.txt

  # Start FastAPI server using nohup to keep it running in background,
  # redirect stdout and stderr to campaign_agent.log file
  nohup python3 main.py > campaign_agent.log 2>&1 &

  echo "✅ Deployment complete!"   # Deployment finish message
'
