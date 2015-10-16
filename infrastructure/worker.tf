resource "google_compute_instance" "disque-worker" {
  name          = "dqworker-${count.index}"
  description   = "The VM hosting the rq workers"
  machine_type  = "n1-standard-1"
  zone          = "us-central1-b"
  tags          = ["memex", "linkalytics", "disque", "worker"]

  disk {
      image = "debian-8-jessie-v20150915"
  }

  metadata {
    sshKeys = "ansible:${file("keys/gce.pub")}"
  }

  network_interface {
      network = "default"
      access_config {}
  }

  count = 3
}
