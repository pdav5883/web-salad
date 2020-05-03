# web-salad
Play some salad bowl online

## Tags
- `v0.1`: Initial working version
- `v0.2`: Minor game experience modifications (button size, sound alerts, update buttons)


## Local Execution
Run `export FLASK_APP=app.py` and `flask run`. By default serve at `localhost:5000`.

## Deployment
Run `zip -r web-salad.zip app.py data static templates utils.py` to create zip file.

Upload `web-salad.zip` to S3 `{your-bucket}` bucket through GUI or with `aws s3 cp web-salad.zip s3://{your-bucket}/web-salad.zip`

Create EC2 instance with IAM role `ec2-web-salad-deploy` (read access into bucket) and security group with http (80) and ssh (22) open inbound from all (0.0.0.0/0)

SSH into the EC2 instance and run 
- `sudo yum install python3`
- `sudo pip3 install flask`
- `mkdir v{version}`
- `cd v{version}`
- `aws s3 cp s3://{your-bucket}/v{version}/web-salad.zip .`
- `unzip web-salad.zip`
- `sudo python3 app.py`

In Route53 update the IPv4 record set for `salad.{your-domain}` to the public IPv4 of the EC2 instance running the server.

## WIP
- Way to constrain teams so pairs are separated
- Add game length to end stats
- If there is time remaining between rounds and next round is shorter time, use diff or ratio
- Consider cache for num words remaining, score, end of game stats, etc
- Include message with "bad" page
- Add game details to admin panel
- Delete games from admin panel
- Change all ../static paths to /static
- Organize style sheet
- Production server
- Running in EC2 without active SSH
- Razzle dazzle
