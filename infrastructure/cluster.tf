resource "google_compute_instance" "linkalytics" {
  name          = "linkalytics"
  description   = "The VM hosting our API"
  machine_type  = "n1-standard-1"
  zone          = "us-central1-b"
  tags          = ["memex", "linkalytics", "api-server"]

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
}
