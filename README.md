# web-salad
A web application to play remote Salad Bowl.

## Tags
- `v0.1`: Initial working version
- `v0.2`: Minor game experience modifications (button size, sound alerts, update buttons)
- `v0.3`: Updated data model to SQLite
- `v1.0`: Updated styling and production deployment

## Local Execution (i.e. not available over internet)
Create a virtualenv with `python >= 3.7` and `flask` installed. Execute `flask run` to serve the app at `localhost:5000`. Use any web browser to navigate to this location from the local machine.

Alternatively run `python app.py` to serve via http. Other machines on the same network will be able to visit the application by going to the local IP address of the host machine (usually begins with `192.168`).

## Deployment (i.e. available over internet)
### Packaging
Run `zip -r web-salad.zip app.py app.wsgi model.py reset_db.py utils.py _version.py data static templates` to create zip file for deployment.

Upload `web-salad.zip` to S3 `{your-bucket}` bucket through GUI or with `aws s3 cp web-salad.zip s3://{your-bucket}/v{version}/web-salad.zip`

### DNS
In AWS Route53 update the IPv4 record set for `salad.{your-domain}` to the public IPv4 of the EC2 instance (see below) running the server.

### Server Option 1: Flask Development Server
This deployment uses the Flask development server to serve the application, and is probably just fine for the use case, despite the Flask warning.

Create an EC2 instance from the **Amazon Linux 2 AMI** with IAM role `ec2-web-salad-deploy` (read access into bucket) and security group with http (80) and ssh (22) open inbound from all (0.0.0.0/0). All other settings are default.

SSH into the EC2 instance (user is ec2-user@) and run:
- `sudo yum update`
- `sudo yum install python3`
- `sudo pip3 install flask`
- `mkdir v{version}`
- `cd v{version}`
- `aws s3 cp s3://{your-bucket}/v{version}/web-salad.zip .`
- `unzip web-salad.zip`
- `python3 reset_db.py`
- `sudo python3 app.py >> salad.log 2>&1 &`

This last command will deattach the server process from the session so you can exit SSH without killing the application. Logs will be written to `salad.log`. To kill the server later, SSH back into the instance and run `sudo ps -ef | grep "python3 app.py"` to get the PIDs of the server, then `sudo kill -9 {PID1} {PID2}` substituting in the PIDs of the `python3 app.py` and `sudo python3.py` processes.

### Server Option 2: WSGI Production Server
This deployment is considerably more complicated and likely completely unnecessary, but is closer to the "right" way of doing things. This process is based on two references [here](https://medium.com/@jQN/deploy-a-flask-app-on-aws-ec2-1850ae4b0d41) and [here](https://pypi.org/project/mod-wsgi/).

Create an EC2 instance from the **Ubuntu 18.04 AMI** with IAM role `ec2-web-salad-deploy` (read access into bucket) and security group with http (80) and ssh (22) open inbound from all (0.0.0.0/0). All other settings are default.

First SSH into the instance (user is ubuntu@) and get the code:
- `sudo apt update`
- `sudo apt install awscli unzip`
- `mkdir v{version}`
- `cd v{version}`
- `aws s3 cp s3://{your-bucket}/v{version}/web-salad.zip .`
- `unzip web-salad.zip`

Install apache server (without WSGI, which will be built later):
- `sudo apt install apache2 apache2-dev`

Test to make sure that the server installed correctly by navigating a browser to the public DNS of the instance (something like `ec2-XX-XX-XX-XX.compute1.amazonaws.com`). You should get an Apache "It works" page.

Here's where the fun starts. Since web-salad uses dataclasses in the model, it requires at least python 3.7 to run. The default python3 installation on the AMI is 3.6.9. Further, WSGI (the apache module used to serve python apps) is built with python 2. So we need to 1) get the right version of python installed, 2) build the WSGI module with that version of python, 3) link that built module to the apache server, and 4) point the server to the flask application.

First let's get python installed:
- `sudo apt install python3.7 python3.7-dev python3.7-venv python3-venv`

Create a virtual environment with the correct python version and pip install dependencies:
- `cd ~`
- `python3.7 -m venv venv`
- `source venv/bin/activate`
- `python --version` (make sure this is `3.7.X`)
- `pip install pip setuptools -U`
- `pip install wheel flask`
- `pip install mod_wsgi`

If anything goes wrong it will be in the `mod_wsgi` install. Make sure the install doesn't show any build error messages, even if the package is installed in pip. Check that the install worked by running `mod_wsgi-express start-server` and making sure the server starts.

Now we need to copy the module that python just built into apache. This command needs to be run as superuser, but for some reason sudo does not recognize the command, so run:
- `sudo su`
- `source venv/bin/activate`
- `mod_wsgi-express install-module`
- `exit`

That command will output two lines similar to:
- `LoadModule wsgi_module "/usr/lib/apache2/modules/mod_wsgi-py37.cpython-37m-x86_64-linux-gnu`.so"
- `WSGIPythonHome "/home/ubuntu/venv"`

Copy these two lines before the #vim line at the end of `/etc/apache2/apache2.conf` (need to use `sudo nano` to edit)/

Now that WSGI is installed and configured, we need to point the server to the application. Link the application to the apache directory with:
- `sudo ln -sT ~/v{version} /var/www/html/web-salad`

Add the following block to the apache site config file `/etc/apache2/sites-enabled/000-default.conf` immediately after the `DocumentRoot /var/www/html` line with `sudo nano`:
```
WSGIDaemonProcess web-salad threads=5
WSGIScriptAlias / /var/www/html/web-salad/app.wsgi
<Directory web-salad>
    WSGIProcessGroup web-salad
    WSGIApplicationGroup %{GLOBAL}
    Order deny,allow
    Allow from all
</Directory>
```

Finally, reset the database and make sure that the server has write permission (not required in Option 1 since it is run with sudo):
- `cd ~/v{version}`
- `python reset_db.py`
- `chmod a+w data data/salad.db`

Now restart with apache server with `sudo service apache2 restart` and visit the Public DNS to make sure the welcome page is served.

If something goes wrong error logs are written to `/var/log/apache2/error.log`

## WIP
- Future
    - Add game length to end stats
    - Consider cache for num words remaining, score, end of game stats, etc
    - Include message with "bad" page
    - Add game details to admin panel
    - Delete games from admin panel
    - Razzle dazzle
    - Don't allow multiple players with the same name in single game
