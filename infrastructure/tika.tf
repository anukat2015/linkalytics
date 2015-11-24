resource "google_compute_instance" "tika-server" {
  name          = "tika-${count.index}"
  description   = "The VM hosting a tika server"
  machine_type  = "n1-highmem-2"
  zone          = "us-central1-b"
  tags          = ["memex", "linkalytics", "tika", "server"]

  disk {
      image = "debian-8-jessie-v20150915"
      size  = 20
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
