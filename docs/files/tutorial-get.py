"""Code for ``tutorial-get.rst`` file."""
import resdk

# Create a Resolwe object to interact with the server and login
res = resdk.Resolwe(url='https://app.genialis.com')
res.login()

# Enable verbose logging to standard output
resdk.start_logging()

res.data.count()
res.sample.count()

# Get all Collection objects with "RNA-Seq" in their name
res.collection.filter(name__contains='RNA-Seq')

# Get all Processes with category "Align"
res.process.filter(category='Align')

# Filter by using several fields:
from datetime import datetime

res.data.filter(
  status='OK',
  created__gt=datetime(2018, 10, 1),
  created__lt=datetime(2025, 11, 1),
  ordering='-modified',
  limit=3,
)

# Get object by slug
res.sample.get('resdk-example')

# Get a data object:
data = res.data.get('resdk-example-reads')

# Object creator:
data.contributor
# Date and time of object creation:
data.created
# Name
data.name
# List of permissions
data.permissions

data = res.data.get('resdk-example-reads')
data.status
data.process
data.started
data.finished
data.size

# Get data by slug
data = res.data.get('resdk-example-reads')

# Print a list of files
data.files()

# Filter the list of files by file name
data.files(file_name='reads.fastq.gz')

# Filter the list of files by field name
data.files(field_name='output.fastq')

# Get sample by slug
sample = res.sample.get('resdk-example')

# Download the FASTQ reads file into current directory
sample.download(
    file_name='reads.fastq.gz',
    download_dir='./',
)
