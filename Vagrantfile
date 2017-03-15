# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Our EC2 instances run ubuntu 14.04 (trusty)
  config.vm.box = "ubuntu/trusty64"

  config.vm.provider "virtualbox" do |v|
    # Seems to be required for Ubuntu
    # https://www.virtualbox.org/manual/ch03.html#settings-processor
    v.customize ["modifyvm", :id, "--pae", "on"]
    # Recommended for Ubuntu
    v.cpus = 2
    # This VM comes without swap memory enabled, so we need to bump up
    # from 512 in order to accomodate installation of lxml
    v.memory = 1024
  end

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network :forwarded_port, guest: 80, host: 8080
  config.vm.network :forwarded_port, guest: 8000, host: 8000, auto_correct: true

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network :private_network, ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network :public_network

  # If true, then any SSH connections made will enable agent forwarding.
  # Default value: false
  
  config.ssh.forward_agent = true

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provisioning
  # -------------
  config.vm.provision :shell, path: "vagrant/provision.sh"

end
