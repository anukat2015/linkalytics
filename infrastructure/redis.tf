resource "google_compute_instance" "redis-node" {
  name          = "redis-${count.index}"
  description   = "The VM hosting a redis instance"
  machine_type  = "n1-highmem-2"
  zone          = "us-central1-b"
  tags          = ["memex", "linkalytics", "redis", "server"]

  disk {
      image = "debian-8-jessie-v20150915"
      size  = 10
  }

  metadata {
    sshKeys = "ansible:${file("keys/gce.pub")}"
  }

  network_interface {
      network = "default"
      access_config {}
  }

  count = 1
}
