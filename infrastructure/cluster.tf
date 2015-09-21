resource "google_compute_disk" "default" {
    name = "redis-disk"
    zone = "us-central1-a"
    size = 500
}

resource "google_compute_instance" "redis-db" {
    name = "redis-queue"
    description = "The VM hosting the redis db"
    machine_type = "n1-standard-1"
    zone = "us-central1-a"
    tags = ["memex", "linkht", "queue"]

    disk {
        image = "debian-8-jessie-v20150915"
    }

    disk {
        disk = "redis-disk"
        device_name = "redis-disk"
        auto_delete = false
    }

    metadata {
      sshKeys = "ansible:${file("keys/gce.pub")}"
    }

    network_interface {
        network = "default"
        access_config {}
    }
}

resource "google_container_cluster" "rqworkers" {
    name = "rq-worker-gke"
    zone = "us-central1-a"
    initial_node_count = 3
    description = "Kubernetes cluster for hosting rqworkers"

    master_auth {
        username = "qadium-user"
        password = "qadium-password-yay"
    }
}
