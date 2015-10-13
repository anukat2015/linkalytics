# What is this?
This directory contains all the files needed to run Terraform to spin up
machines on GCE. It also contains the Ansible files needed to install the
linkalytics project onto those nodes.

If you don't want all the gory details, you can install [Terraform][] and [Ansible][] and skip to the [summary][]

## Terraform
[Terraform][] is a tool to create VMs in remote cloud services such as AWS, GCE, and DigitalOcean. We use `terraform apply` to provision blank VMs on GCE. This folder contains all the files needed to provision blank VMs on GCE with the exception of

You'll need to generate the following:

* `account.json` -- This is the JSON file containing credentials for your GCE account, please check out the Terraform website for details on generating the [account.json][] file.
* `keys/gce.pub` -- This is the expected path for the public SSH key for [Ansible][] associated with the "ansible" user.
* `keys/gce` -- This is the corresponding private SSH key for [Ansible][] associated with the "ansible" user.

Here's how to generate the SSH keys:

    cd linkalytics/infrastructure
    mkdir keys
    ssh-keygen -t rsa -C "example_label" (and save the key named "gce" in the keys folder)

Once you create those files, you can create infrastructure that mirrors ours.

    terraform apply -var gce_project=$YOUR_PROJECT_ID

## Ansible
[Ansible][] is a tool to provision VMs via SSH. It uses SSH to log into machines and runs shell scripts (or other kinds of programs) to install dependencies or binaries to bring a fresh VM into a known state.

    ansible-playbook -i terraform.py -s -u ansible --private-key=`pwd`/keys/gce ansible/disque.yml

In order to know which machines to SSH into, Ansible uses an *inventory*. This inventory can be static (listed by hand) or dynamic; the file `terraform.py` allows Ansible to use information from Terraform in its inventory. This is the argument to the `-i` flag.

The `-s` flag tells `ansible-playbook` to run as a super-user; the `-u` flag tells `ansible-playbook` which user to use (in this case, `ansible`); the `--private-key` flag tells `ansible-playbook` where to find the private SSH key; and the positional argument `ansible/server.yml` tells `ansible-playbook` the sequence of tasks (*i.e.*, the "playbook") to run on the remote machines.

## Summary
Install the dependencies, set up credentials, and run
```
terraform apply -var gce_project=$YOUR_PROJECT_ID
ansible-playbook -i terraform.py -s -u ansible --private-key=`pwd`/keys/gce -v ansible/server.yml
```

[terraform]:     https://terraform.io  "Terraform"
[account.json]:  https://terraform.io/docs/providers/google/index.html "account.json"
[ansible]:       http://ansible.com    "Ansible"
[summary]:       #summary              "Summary"
