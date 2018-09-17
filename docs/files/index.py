"""Code used in ``index.rst`` file."""
import resdk

# Create a Resolwe object to interact with the server
res = resdk.Resolwe(url='https://app.genialis.com')

# Enable verbose logging to standard output
resdk.start_logging()

# Get sample meta-data from the server
sample = res.sample.get('resdk-example')

# Download files associated with the sample
sample.download()
