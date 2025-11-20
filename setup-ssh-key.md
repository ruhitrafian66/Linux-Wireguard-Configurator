# SSH Key Setup Instructions

Your SSH key has been generated! Now you need to add it to your Debian VM.

## Option 1: Manual Setup (Recommended)

1. **Log into your VM directly** (using console or existing connection):
   ```bash
   ssh root@10.211.55.4
   # Enter password: root
   ```

2. **On the VM, run these commands**:
   ```bash
   # Create .ssh directory if it doesn't exist
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   
   # Add your public key to authorized_keys
   echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIED9j1aH6YLsCYqGKb/aapXLgZsMAkv9ezyEnSUByrpO wireguard-deployment" >> ~/.ssh/authorized_keys
   
   # Set correct permissions
   chmod 600 ~/.ssh/authorized_keys
   
   # Ensure SSH password authentication is enabled (if needed)
   sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
   sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
   systemctl restart sshd
   ```

3. **Test the connection from your Mac**:
   ```bash
   ssh root@10.211.55.4
   # Should connect without password!
   ```

## Option 2: Copy-Paste Method

If you can access the VM console directly:

1. Open VM console and login as root
2. Run:
   ```bash
   mkdir -p ~/.ssh && chmod 700 ~/.ssh
   nano ~/.ssh/authorized_keys
   ```
3. Paste this public key:
   ```
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIED9j1aH6YLsCYqGKb/aapXLgZsMAkv9ezyEnSUByrpO wireguard-deployment
   ```
4. Save (Ctrl+O, Enter, Ctrl+X)
5. Run:
   ```bash
   chmod 600 ~/.ssh/authorized_keys
   ```

## After Setup

Once the SSH key is configured, run the deployment:
```bash
./deploy.sh
```

The deployment script will now work without password prompts!
