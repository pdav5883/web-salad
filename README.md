# web-salad
Play some salad bowl online


## Local Execution
Run `export FLASK_APP=app.py` and `flask run`. By default serve at `localhost:5000`.

## Deployment
Run `zip -r web-salad.zip app.py data static templates utils.py` to create zip file.

Upload `web-salad.zip` to S3 `web-salad-deployment` bucket through GUI or with `aws s3 cp web-salad.zip s3://web-salad-deployment/web-salad.zip`

Create EC2 instance with IAM role `ec2-web-salad-deploy` (read access into bucket) and security group with http (80) and ssh (22) open inbound from all (0.0.0.0/0)

SSH into the EC2 instance and run 
- `sudo yum install python3`
- `sudo pip3 install flask`
- `mkdir v{version}`
- `cd v{version}`
- `aws s3 cp s3://web-salad-deployment/web-salad.zip`
- `unzip web-salad.zip`
- `sudo python3 app.py`

In Route53 update the IPv4 record set for `salad.bearloves.rocks` to the public IPv4 of the EC2 instance running the server.