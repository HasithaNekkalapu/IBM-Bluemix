# Name : Hasitha Nekkalapu
# Course Number : CSE 6331
# Lab Number : Assignment 1

from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify
import atexit
import os
import json
import cf_deployment_tracker
import keystoneclient.v3 as keystoneclient
import swiftclient.client as swiftclient
import gnupg
import pdb
import glob
import getpass

# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

#List all files in current directory
pathname = ''
print glob.glob(pathname)
pswd = getpass.getpass('Enter 4 digit encryption key:')
file_name=raw_input('Enter the name of file to encrypt:')

#authentication data
auth_url = 'https://identity.open.softlayer.com/v3'
password = 'NbgeEFGK=L~3?c0_'
project_id = 'projectid'
user_id = 'userid'
region_name ='region-name'
conn = swiftclient.Connection(
	key=password,
	authurl=auth_url,
	auth_version='3',
	os_options={
		"project_id": project_id,
		"user_id": user_id,
		"region_name": region_name
	})
# Creating and Adding Container-Name in Bluemix 
container_name = 'text-container'
other_container = 'others'
conn.put_container(other_container)
conn.put_container(container_name)

# Creating and adding file to container for encryption
print ("File Name is, %s." % file_name)
istextfile = file_name.split('.')
print istextfile[1]

#Encrypt File usinh gnupg
gpg = gnupg.GPG(gnupghome = os.getcwd() + '/.gnupg')
input_data = gpg.gen_key_input(key_type="RSA", key_length=1024, phrases = '')
key = gpg.gen_key(input_data)
print("File encrypted locally")

#Decrypt locally
writefile = "temp-copy.txt";
decryptfile = raw_input('Do you want to decrypt file? yes/no: ')
if decryptfile == 'yes':
    file = open(writefile)
    fileContent = file.read()
    decrypted_content = gpg.decrypt(fileContent, passphrase=pswd)
    decryptedFileName = 'decrypted.txt'
    decFile = open(decryptedFileName,'w')
    decFile.write(str(decrypted_content))
    decFile.close()
    print('File Decrypted Locally')

#Encrypted File  - We could remove it as well from local once upload is complete
encrypted_file = 'encrypted_'+file_name
downloadfilename = 'encrypted_'+file_name

with open(file_name, 'rb') as f:
	status = gpg.encrypt_file(f, None, passphrase=pswd,symmetric='AES256', output=encrypted_file)

encrypted_file_read = open(encrypted_file)
encrypted_filecontents=encrypted_file_read.read()


# Create a file for uploading
uploadfile = raw_input('Do you want to upload file to cloud storage? yes/no: ')
if uploadfile == 'yes':
        count = 0
        for container in conn.get_account()[1]:
                for data in conn.get_container(container['name'])[1]:
                        print 'dataaa nameeee            '+data['name']+'      encrypted file nameeeee      '+encrypted_file
                        if encrypted_file == data['name']:
                                print 'true'
                                count = count+1
                                encrypted_file = str(count)+encrypted_file
                                print count

        print count
        if count>0:
                if istextfile[1] == 'txt' :
                        conn.put_object(container_name, str(count)+encrypted_file, contents= encrypted_filecontents, content_type='text/plain')
                else :
                        conn.put_object(other_container, str(count)+encrypted_file, contents= encrypted_filecontents, content_type='')
        else :
                if istextfile[1] == 'txt' :
                        conn.put_object(container_name, encrypted_file, contents= encrypted_filecontents, content_type='text/plain')
                else:
                        conn.put_object(other_container, str(count)+encrypted_file, contents= encrypted_filecontents, content_type='')
        print ('\n File Uploaded.')

# Download File again

        downloadfile = raw_input('Do you want to download file from cloud storage? yes/no: ')
        if downloadfile == 'yes':
                new_file = conn.get_object(container_name, downloadfilename)

                download_file = open( writefile, 'wb')
                download_file.write(new_file[1])
                download_file.close()

        print ('File Downloaded')

#decrypt - file

file = open(writefile)
fileContent = file.read()
decrypted_content = gpg.decrypt(fileContent, passphrase='hasitha-cloud')

decryptedFileName = 'decrypted_'+file_name
decFile = open(decryptedFileName,'w')
decFile.write(str(decrypted_content))
decFile.close()

print ('File Content Download at local directory')
print (decrypted_content)


# List your containers
print ("\nContainer List:")

for container in conn.get_account()[1]:
    print (container['name'])

# List objects in a container, and prints out each object name, the file size, and last modified date

print ("\n Object List:")

for container in conn.get_account()[1]:
    for data in conn.get_container(container['name'])[1]:
        print ('object: {0}\t size: {1}\t date: {2}'.format(data['name'], data['bytes'], data['last_modified']))
        print conn.get_account()[1][0]["count"]
        
# Delete the file from Container
deletefile = raw_input('Delete file? yes/no: ')
if deletefile.lower() == 'yes':
        conn.delete_object(container_name, 'encrypted.txt')

# List objects in a container, and prints out each object name, the file size, and last modified date

print ("\n Object List:")

for container in conn.get_account()[1]:
    for data in conn.get_container(container['name'])[1]:
        print ('object: {0}\t size: {1}\t date: {2}'.format(data['name'], data['bytes'], data['last_modified']))
        print conn.get_account()[1][0]["count"]
# On Bluemix, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('PORT', 8080))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/testCall', methods=['GET'])
def test():
    return  'Working'

if __name__ == '_main_':
    app.run(host='0.0.0.0', port=port, debug=True)
