#!/usr/bin/expect -f

# Automated deployment using expect
set timeout 60
set vm_ip "10.211.55.4"
set vm_user "root"
set vm_pass "root"

# Copy the deployment script
spawn scp -o StrictHostKeyChecking=no deploy-manual.sh ${vm_user}@${vm_ip}:/tmp/
expect {
    "password:" {
        send "${vm_pass}\r"
        expect eof
    }
}

# Execute the deployment script
spawn ssh -o StrictHostKeyChecking=no ${vm_user}@${vm_ip} "chmod +x /tmp/deploy-manual.sh && /tmp/deploy-manual.sh"
expect {
    "password:" {
        send "${vm_pass}\r"
        interact
    }
}
