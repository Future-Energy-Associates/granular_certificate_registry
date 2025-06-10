# EventStore DB Deployment on GCP VM

This guide outlines the process for deploying EventStore DB on a Google Cloud Platform (GCP) compute engine with additional persistent storage.

## 1. Update Environment and Install Docker

*Set up the base environment with necessary packages:*

- `sudo apt-get update`
- `sudo apt-get install -y docker.io docker-compose`
- `sudo usermod -aG docker $USER`

## 2. Create and Attach Persistent Disk

*Create a persistent SSD disk and attach it to the instance:*

- `gcloud compute disks create eventstore-data-disk --size=100GB --type=pd-ssd --zone=us-east1-c`
- `gcloud compute instances attach-disk event-store --disk=eventstore-data-disk --zone=us-east1-c`

## 3. Format and Mount Disk

*Format the disk, create a mount point, and configure it for persistence:*

- `sudo mkfs.ext4 -m 0 -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/sdb`
- `sudo mkdir -p /mnt/eventstore`
- `sudo mount -o discard,defaults /dev/sdb /mnt/eventstore`
- `echo UUID=$(sudo blkid -s UUID -o value /dev/sdb) /mnt/eventstore ext4 discard,defaults 0 2 | sudo tee -a /etc/fstab`

## 4. Create Storage Directories

*Set up directories for EventStore data and logs with proper permissions:*

- `sudo mkdir -p /mnt/eventstore/data`
- `sudo mkdir -p /mnt/eventstore/logs`
- `sudo chown -R 1000:1000 /mnt/eventstore`

## 5. Deploy EventStore with Docker Compose

*Create and start the EventStore container:*

- `sudo nano docker-compose.yml`
- `sudo docker-compose up -d`
- `curl http://localhost:2113/info`

## 6. Configure Network Access

*Set up networking to allow access to EventStore:*

- `gcloud compute networks vpc-access connectors create registry-vpc --network=default --region=us-east1 --range=10.8.0.0/28`
- `gcloud run services update api --region=us-east1 --vpc-connector=registry-vpc`
- `gcloud compute firewall-rules create allow-cloudrun-to-eventstore --direction=INGRESS --priority=1000 --network=default --action=ALLOW --rules=tcp:2113 --source-ranges=10.8.0.0/28 --target-tags=eventstore`
- `gcloud compute instances add-tags event-store --tags=eventstore --zone=us-east1-c`
- `gcloud run services update api --region=us-east1 --ingress=all`

## 7. Data Inspection

*Commands for checking event data:*

- `gcloud compute scp event-store:/mnt/eventstore/data/chunk-000000.000000 ./eventstore-chunk.bin --zone=us-east1-c`
- `strings eventstore-chunk.bin > readable_content.txt`